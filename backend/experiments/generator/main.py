import datetime
import typer
import os
import time
import uuid
import json
from datetime import timedelta
from multiprocessing import Pool, cpu_count
from functools import partial
import logging
import locale
import random
from faker import Faker

app = typer.Typer()

from utils.string_helper import (
    get_kabupaten,
    get_kecamatan,
    get_kelurahan,
    get_name,
    get_nik,
    get_provinsi,
    get_random_no_hp,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.command()
def extract_variables():
    from utils.document_processor import extract_variables_from_template

    template_path = os.path.join(os.getcwd(), "storage/templates/docx")

    for file in os.listdir(template_path):
        try:
            if file.endswith(".docx"):
                variables = extract_variables_from_template(
                    os.path.join(template_path, file)
                )
                variables_path = os.path.join(
                    os.getcwd(),
                    "storage/templates/variables",
                    f'{file.removesuffix(".docx")}.json',
                )
                with open(variables_path, "w") as f:
                    json.dump(variables, f)
        except Exception as e:
            print(f"Error processing file {file}: {str(e)}")


def _process_single_document(args):
    """
    Worker function untuk memproses satu dokumen.
    Digunakan oleh multiprocessing pool.
    """
    from utils.document_processor import process_template, convert_docx_to_pdf

    template_path, docname, variables, output_dir, index, use_word = args

    try:
        # Generate unique filename dengan microseconds untuk menghindari collision
        timestamp = datetime.datetime.now()
        output_filename = (
            timestamp.strftime("%Y-%m-%d_%H%M%S") + f"_{timestamp.microsecond}_{index}"
        )

        docx_output_file = os.path.join(output_dir, f"{output_filename}.docx")
        pdf_output_file = os.path.join(output_dir, f"{output_filename}.pdf")
        json_output_file = os.path.join(output_dir, f"{output_filename}.json")

        # Save variables to JSON
        with open(json_output_file, "w") as f:
            json.dump(variables, f)

        # Process template
        process_template(template_path, docx_output_file, variables)

        # Convert to PDF
        if use_word:
            # Use Microsoft Word (requires permission granted)
            convert_docx_to_pdf(
                docx_output_file, pdf_output_file, skip_docx2pdf=False, prefer_word=True
            )
        else:
            # Use LibreOffice (default)
            convert_docx_to_pdf(docx_output_file, pdf_output_file)

        # Remove intermediate docx file
        if os.path.exists(docx_output_file):
            os.remove(docx_output_file)

        return {"success": True, "file": pdf_output_file, "docname": docname}

    except Exception as e:
        logger.error(f"Error processing document {docname} (index {index}): {str(e)}")
        return {"success": False, "error": str(e), "docname": docname, "index": index}


@app.command()
def generate_documents(
    count: int = 1,
    workers: int = None,
    show_progress: bool = True,
    use_word: bool = False,
    template: str = None,
):
    """
    Generate documents dengan multiprocessing untuk performa optimal.

    Args:
        count: Jumlah dokumen yang akan di-generate per template
        workers: Jumlah worker processes (default: CPU count - 1, or unlimited if use_word)
        show_progress: Tampilkan progress bar
        use_word: Use Microsoft Word instead of LibreOffice (requires permission granted)
    """
    from utils.document_processor import process_template, convert_docx_to_pdf

    start_time = time.time()

    # Determine optimal number of workers
    if workers is None:
        if use_word:
            # Microsoft Word is more stable, can use more workers
            workers = max(1, cpu_count() - 1)
        else:
            # LibreOffice needs limitation to prevent crashes
            workers = min(4, max(1, cpu_count() - 1))

    converter_info = (
        "Microsoft Word (no limit)"
        if use_word
        else "LibreOffice (limited to 3 concurrent)"
    )
    logger.info(
        f"Starting document generation with {workers} workers using {converter_info}"
    )

    storage_templates = os.path.join(os.getcwd(), "storage/templates/docx")

    switcher = {
        "letter_template": _letter_template_values,
        "table_template": _invoice_template_values,
        "form_template": _form_template_values,
        "mixed_template": _report_template_values,
        "certificate_template": _certificate_template_values,
    }

    if template:
        switcher = {template: switcher.get(template)}

    # Create output directories
    for directory in switcher.keys():
        try:
            os.makedirs(
                os.path.join(os.getcwd(), "storage/output", directory), exist_ok=True
            )
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {str(e)}")

    # Prepare tasks for multiprocessing
    tasks = []
    template_files = [f for f in os.listdir(storage_templates) if f.endswith(".docx")]

    for file in template_files:
        docname = file.removesuffix(".docx")
        template_path = os.path.join(storage_templates, file)
        output_dir = os.path.join(os.getcwd(), "storage/output", docname)

        # Get the value generator function
        value_generator = switcher.get(docname)
        if value_generator is None:
            continue

        # Create tasks for each document instance
        for i in range(count):
            variables = value_generator()
            tasks.append((template_path, docname, variables, output_dir, i, use_word))

    total_tasks = len(tasks)
    # logger.info(f"Total documents to generate: {total_tasks}")

    if total_tasks == 0:
        logger.warning("No documents to generate")
        return

    # Process documents in parallel
    results = []
    with Pool(processes=workers) as pool:
        if show_progress:
            # Process with progress tracking
            for i, result in enumerate(
                pool.imap_unordered(_process_single_document, tasks), 1
            ):
                results.append(result)
                # if i % 10 == 0 or i == total_tasks:
                # logger.info(
                #     f"Progress: {i}/{total_tasks} documents processed ({i*100//total_tasks}%)"
                # )
        else:
            # Process without progress tracking
            results = pool.map(_process_single_document, tasks)

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = total_tasks - successful

    elapsed_time = time.time() - start_time

    logger.info("=" * 60)
    logger.info("Document Generation Summary")
    logger.info("=" * 60)
    logger.info(f"Total documents: {total_tasks}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Workers used: {workers}")
    logger.info(f"Time elapsed: {elapsed_time:.2f} seconds")
    logger.info(f"Average time per document: {elapsed_time/total_tasks:.2f} seconds")
    logger.info("=" * 60)

    if failed > 0:
        logger.warning("\nFailed documents:")
        for result in results:
            if not result["success"]:
                logger.warning(
                    f"  - {result['docname']} (index {result['index']}): {result['error']}"
                )


def _letter_template_values():

    fake = Faker("id_ID")
    desa = get_kelurahan()
    kecamatan = get_kecamatan(id=desa.get("kecamatan_id"))
    kabupaten = get_kabupaten(id=kecamatan.get("kabupaten_id"))
    tempat_lahir = get_kabupaten()
    gender = fake.random_element(elements=("Laki-Laki", "Perempuan"))
    usia = fake.random_int(min=18, max=55)
    date_of_birth = datetime.datetime.now() - timedelta(days=usia * 365)
    nik = get_nik(gender, date_of_birth, kabupaten_id=tempat_lahir.get("id"))

    agama = fake.random_element(
        elements=("Islam", "Kristen", "Hindu", "Buddha", "Konghucu")
    )
    status_perkawinan = fake.random_element(
        elements=("Kawin", "Belum Kawin", "Pernah Kawin")
    )
    tempat_lahir = get_kabupaten()

    tanggal_sign = fake.date_between(start_date="-2y", end_date="-1d")

    # desa first character every word
    nick_desa = "".join([word[0] for word in desa.get("name").split(" ")])

    nomor_surat = (
        str(fake.random_int(min=1, max=999)).zfill(5)
        + "/"
        + nick_desa.upper()
        + "/"
        + tanggal_sign.strftime("%m/%Y")
    )

    rt = fake.random_int(min=1, max=99)
    rw = fake.random_int(min=1, max=99)

    return {
        "kabupaten_kop": kabupaten.get("name").upper(),
        "kecamatan_kop": kecamatan.get("name").upper(),
        "desa_kop": desa.get("name").upper(),
        "alamat_kantor_desa": fake.street_address(),
        "telp_kantor_desa": fake.phone_number(),
        "nomor_surat": nomor_surat,
        "desa": desa.get("name").title(),
        "kecamatan": kecamatan.get("name").title(),
        "kabupaten": kabupaten.get("name").title(),
        "nik": nik,
        "nama_lengkap": get_name(gender=gender, with_title=False),
        "tempat_lahir": tempat_lahir.get("name").title(),
        "tanggal_lahir": date_of_birth.strftime("%d-%m-%Y"),
        "jenis_kelamin": gender,
        "pekerjaan": fake.job(),
        "agama": agama,
        "status_kawin": status_perkawinan,
        "alamat": fake.street_address()
        + " RT."
        + str(rt).zfill(3)
        + " RW."
        + str(rw).zfill(3),
        "keperluan": fake.sentence(nb_words=3)
        .replace(".", "")
        .replace("!", "")
        .replace("?", "")
        .replace(",", ""),
        "tanggal_surat": tanggal_sign.strftime("%d-%m-%Y"),
        "kepala_desa": get_name(with_title=False),
    }


def _form_template_values():
    fake = Faker("id_ID")

    gender = fake.random_element(elements=("Laki-Laki", "Perempuan"))
    usia = fake.random_int(min=18, max=45)
    date_of_birth = datetime.datetime.now() - timedelta(days=usia * 365)
    desa = get_kelurahan()
    kecamatan = get_kecamatan(id=desa.get("kecamatan_id"))
    kabupaten = get_kabupaten(id=kecamatan.get("kabupaten_id"))
    tempat_lahir = get_kabupaten()
    nik = get_nik(gender, date_of_birth, kabupaten_id=tempat_lahir.get("id"))

    return {
        "nik": nik,
        "nama_lengkap": get_name(gender=gender, with_title=False),
        "jenis_kelamin": gender,
        "tempat_lahir": tempat_lahir.get("name").title(),
        "tanggal_lahir": date_of_birth.strftime("%d-%m-%Y"),
        "alamat": fake.street_address(),
        "desa": desa.get("name").title(),
        "usia": str(usia),
        "kecamatan": kecamatan.get("name").title(),
        "kabupaten": kabupaten.get("name").title(),
        "no_hp": get_random_no_hp(),
        "email": fake.email(),
        "kabupaten_daftar": get_kabupaten().get("name").title(),
        "tanggal_daftar": fake.date_between(start_date="-2y", end_date="-1d").strftime(
            "%d-%m-%Y"
        ),
        "status_kawin": fake.random_element(
            elements=("Belum Kawin", "Kawin", "Pernah Kawin")
        ),
    }


def _report_template_values():
    fake = Faker("en_US")

    project_name = fake.bs()
    project_location = fake.city()
    survey_date = fake.date_between(start_date="-2y", end_date="-1d")
    surveyor_name = get_name(with_title=False)
    client_name = fake.company()

    return {
        "project_name": project_name,
        "project_location": project_location,
        "survey_date": survey_date.strftime("%B %d, %Y"),
        "surveyor_name": surveyor_name,
        "client_name": client_name,
        "survey_date_2": survey_date.strftime(
            "%B %d, %Y"
        ),  # ✅ Keep same format as survey_date
        "project_location_2": project_location,  # ✅ Keep full value, same as project_location
        "client_name_2": client_name,  # ✅ Keep full value, same as client_name
        "area_id_1": fake.sbn9(separator=""),
        "area_finding_1": fake.sentence(nb_words=4),
        "area_recomendation_1": fake.sentence(nb_words=9),
        "area_id_2": fake.sbn9(separator=""),
        "area_finding_2": fake.sentence(nb_words=4),
        "area_recomendation_2": fake.sentence(nb_words=9),
        "area_id_3": fake.sbn9(separator=""),
        "area_finding_3": fake.sentence(nb_words=4),
        "area_recomendation_3": fake.sentence(nb_words=9),
        "approver_name": get_name(with_title=False),
        "approver_id": get_nik(),
        "surveyor_name_sign": surveyor_name,
        "surveyor_id": get_nik(),
    }


def _get_course_name():

    # 1. Expanded list of fields of study (Bidang Studi)
    fields_of_study = [
        "Computer Science",
        "Biology",
        "History",
        "Mathematics",
        "Art History",
        "Psychology",
        "Chemistry",
        "Physics",
        "Political Science",
        "Economics",
        "Sociology",
        "Data Science",
        "Cybersecurity",
        "Environmental Science",
        "Business Administration",
        "Software Engineering",
        "Artificial Intelligence",
    ]

    # 2. Expanded list of course types/introductory phrases (Jenis Kursus)
    course_types = [
        "Introduction to",
        "Advanced Studies in",
        "Foundations of",
        "Topics in",
        "Survey of",
        "Seminar on",
        "Principles of",
        "Practical Applications of",
        "Research Methodologies in",
        "The Essentials of",
    ]

    # 3. New variable: Specific Focus/Qualifier (Fokus Spesifik/Kualifikasi)
    specific_focus = [
        "for Beginners",
        "in the 21st Century",
        "with Hands-On Projects",
        "using Python",
        "using Java",
        "using modern techniques",
        "focused on theory",
        "focused on field work",
        "A Global Perspective",
        "The European Context",
        "Case Studies in Industry",
    ]

    field = random.choice(fields_of_study)
    course_type = random.choice(course_types)
    focus = random.choice(specific_focus)
    # Gabungkan ketiganya
    return f"{course_type} {field} {focus}"


def _certificate_number(type: str = "certificate", date: str = "") -> str:
    switcher = {
        "certificate": "CVC",
        "contract": "CTC",
        "invoice": "INV",
        "job_application": "JAP",
        "medical_form": "MVF",
    }
    code = switcher.get(type, lambda: "NBC")

    fake = Faker("id_ID")

    # random padded left 3 number
    nomor = fake.random_int()

    date = fake.date(pattern="%m/%Y") if date == "" else date
    # nomor = str(nomor).zfill(3)
    return f"{nomor}/{code}/{date}"


def _rupiah_format(number: int, with_prefix: bool = False, desimal: int = 0) -> str:
    # number before decimal point should be grouped by 3
    # number after decimal point should be rounded to 2
    # if desimal is 0, then number after decimal point should be rounded to 0
    # add prefix "Rp. " if with_prefix is True
    return f"Rp. {number:,.{desimal}f}" if with_prefix else f"{number:,.{desimal}f}"


def _invoice_template_values():

    fake = Faker("id_ID")

    bahan_pokok = [
        "Beras",
        "Gula",
        "Minyak Goreng",
        "Mentega",
        "Telur Ayam",
        "Telur Bebek",
        "Daging Sapi",
        "Daging Ayam",
        "Susu",
        "Jagung",
        "Gas Elpiji",
        "Garam",
    ]

    item_1_quantity = fake.random_int(min=1, max=100)
    item_1_rate = fake.random_int(min=1, max=100) * 1000
    item_1_amount = item_1_quantity * item_1_rate

    item_2_quantity = fake.random_int(min=1, max=100)
    item_2_rate = fake.random_int(min=1, max=100) * 1000
    item_2_amount = item_2_quantity * item_2_rate

    item_3_quantity = fake.random_int(min=1, max=100)
    item_3_rate = fake.random_int(min=1, max=100) * 1000
    item_3_amount = item_3_quantity * item_3_rate

    # round 2 digit
    subtotal = round(item_1_amount + item_2_amount + item_3_amount)
    diskon = round(subtotal * (fake.random_int(min=1, max=15) / 100))
    ppn11 = round(subtotal * 0.11)
    total = round(subtotal - diskon + ppn11)

    item_1_desc = fake.random_element(elements=bahan_pokok)
    bahan_pokok.remove(item_1_desc)
    item_2_desc = fake.random_element(elements=bahan_pokok)
    bahan_pokok.remove(item_2_desc)
    item_3_desc = fake.random_element(elements=bahan_pokok)
    bahan_pokok.remove(item_3_desc)

    tanggal_invoice = fake.date_between(start_date="-3y", end_date="today")
    tanggal_jatuh_tempo = tanggal_invoice + timedelta(
        days=fake.random_int(min=7, max=60)
    )

    return {
        "nama_pelanggan": get_name(with_title=False),
        "alamat_pelanggan": fake.street_address(),
        "telp_pelanggan": get_random_no_hp(),
        "nomor_invoice": _certificate_number(
            "invoice", tanggal_invoice.strftime("%m/%Y")
        ),
        "tanggal_invoice": tanggal_invoice.strftime("%d-%m-%Y"),
        "tanggal_jatuh_tempo": tanggal_jatuh_tempo.strftime("%d-%m-%Y"),
        "item_description_1": item_1_desc,
        "item_qty_1": str(item_1_quantity),
        "item_harga_1": _rupiah_format(item_1_rate),
        "item_jumlah_1": _rupiah_format(item_1_amount),
        "item_description_2": item_2_desc,
        "item_qty_2": str(item_2_quantity),
        "item_harga_2": _rupiah_format(item_2_rate),
        "item_jumlah_2": _rupiah_format(item_2_amount),
        "item_description_3": item_3_desc,
        "item_qty_3": str(item_3_quantity),
        "item_harga_3": _rupiah_format(item_3_rate),
        "item_jumlah_3": _rupiah_format(item_3_amount),
        "subtotal": _rupiah_format(subtotal),
        "diskon": _rupiah_format(diskon),
        "ppn": _rupiah_format(ppn11),
        "total_akhir": _rupiah_format(total),
        "nama_direktur": get_name(with_title=False),
    }

def _certificate_template_values():

    fake = Faker("en_US")
    id = "CE-" + str(uuid.uuid4())

    event_date = fake.date_between(start_date="-20y", end_date="-1d")

    instructor_name = get_name(with_title=False)
    return {
        "recipient_name": get_name(with_title=False),
        "course_name": _get_course_name(),
        "completed_at": event_date.strftime("%B %d, %Y"),
        "course_hours": fake.random_int(min=24, max=99),
        "instructor_name": instructor_name,
        "instructor_sign": instructor_name,
        "certificate_number": id,
        "certificate_url": fake.url() + id,
        "version": str(fake.random_int(min=1, max=9))
        + "."
        + str(fake.random_int(min=0, max=9))
        + "."
        + str(fake.random_int(min=0, max=9)),
    }


if __name__ == "__main__":
    app()
