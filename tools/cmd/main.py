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

app = typer.Typer()

from utils.string_helper import get_nik, get_random_kabupaten_name, get_random_no_hp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.command()
def extract_variables():
    from utils.document_processor import extract_variables_from_template

    template_path = os.path.join(os.getcwd(), "storage/templates")

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

    storage_templates = os.path.join(os.getcwd(), "storage/templates")

    switcher = {
        "certificate_template": _certificate_template_values,
        "contract_template": _contract_template_values,
        "invoice_template": _invoice_template_values,
        "job_application_template": _job_application_template_values,
        "medical_form_template": _medical_form_template_values,
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
            logger.warning(f"No value generator found for {docname}, skipping...")
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


def _certificate_template_values():
    from faker import Faker

    fake = Faker("id_ID")

    event_date = fake.date_between(start_date="-60w", end_date="-1d")
    issue_date = event_date + timedelta(days=fake.random_int(min=5, max=15))
    event_name = (
        fake.random_element(elements=["Seminar", "Workshop", "Training"])
        + " "
        + fake.job()
    )
    return {
        "recipient_name": fake.name(),
        "event_name": event_name,
        "event_date": event_date.strftime("%d %B %Y"),
        "event_location": fake.address(),
        "issue_place": get_random_kabupaten_name().title(),
        "issue_date": issue_date.strftime("%d %B %Y"),
        "supervisor_name": fake.name(),
        "chairman_name": fake.name(),
        "certificate_number": _certificate_number(
            "certificate", issue_date.strftime("%m/%Y")
        ),
    }


def _certificate_number(type: str = "certificate", date: str = "") -> str:
    switcher = {
        "certificate": "CVC",
        "contract": "CTC",
        "invoice": "INV",
        "job_application": "JAP",
        "medical_form": "MVF",
    }
    code = switcher.get(type, lambda: "NBC")

    from faker import Faker

    fake = Faker("id_ID")

    # random padded left 3 number
    nomor = fake.random_int()

    date = fake.date(pattern="%m/%Y") if date == "" else date
    # nomor = str(nomor).zfill(3)
    return f"{nomor}/{code}/{date}"


def _contract_template_values():
    from faker import Faker

    fake = Faker("id_ID")

    gender = fake.random_element(elements=("Laki-Laki", "Perempuan"))
    date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=65)
    nik = get_nik(gender, date_of_birth)

    start_date = fake.date_between(
        start_date=datetime.date(2022, 1, 1), end_date=datetime.date(2025, 1, 1)
    )
    end_date = start_date + timedelta(days=365)

    return {
        "contract_number": _certificate_number("contract"),
        "contract_date": start_date.strftime("%d %B %Y"),
        "company_name": fake.company(),
        "company_address": fake.address(),
        "company_representative": fake.name(),
        "employee_name": (
            fake.name_male() if gender == "Laki-Laki" else fake.name_female()
        ),
        "employee_nik": nik,
        "employee_address": fake.address(),
        "employee_phone": get_random_no_hp(),
        "position": fake.job_female() if gender == "Perempuan" else fake.job_male(),
        "division": fake.random_element(
            elements=(
                "HRD",
                "IT",
                "FINANCE",
                "MARKETING",
                "SALES",
                "OPERATIONS",
                "PRODUCTION",
                "PURCHASE",
                "SALES",
                "SERVICE",
                "SUPPLY",
                "TECHNICAL",
                "TRAINING",
                "WASTE",
                "WORKING",
            )
        ),
        "start_date": start_date.strftime("%d-%m-%Y"),
        "end_date": end_date.strftime("%d-%m-%Y"),
        "basic_salary": _rupiah_format(fake.random_int(min=3000000, max=10000000)),
        "allowance": _rupiah_format(fake.random_int(min=1000000, max=5000000)),
        "working_hours": fake.random_int(min=8, max=10),
        "annual_leave": fake.random_int(min=11, max=15),
        "probation_period": fake.random_int(min=3, max=6),
    }


def _rupiah_format(number: int) -> str:
    # convert number to rupiah format ex: number = 100000 -> 100.000
    return f"{number:,}".replace(",", ".")


def _invoice_template_values():
    from faker import Faker

    fake = Faker("id_ID")
    id = uuid.uuid4()

    item_1_quantity = fake.random_int(min=1, max=10)
    item_1_rate = fake.random_int(min=10000, max=500000)
    item_1_amount = item_1_quantity * item_1_rate
    item_1_tax = item_1_amount * 0.12

    item_2_quantity = fake.random_int(min=1, max=10)
    item_2_rate = fake.random_int(min=10000, max=500000)
    item_2_amount = item_2_quantity * item_2_rate
    item_2_tax = item_2_amount * 0.12

    item_3_quantity = fake.random_int(min=1, max=10)
    item_3_rate = fake.random_int(min=10000, max=500000)
    item_3_amount = item_3_quantity * item_3_rate
    item_3_tax = item_3_amount * 0.12

    item_4_quantity = fake.random_int(min=1, max=10)
    item_4_rate = fake.random_int(min=10000, max=500000)
    item_4_amount = item_4_quantity * item_4_rate
    item_4_tax = item_4_amount * 0.12

    total_amount = item_1_amount + item_2_amount + item_3_amount + item_4_amount
    total_tax = item_1_tax + item_2_tax + item_3_tax + item_4_tax
    total = total_amount + total_tax

    return {
        "company_name": fake.company(),
        "company_address": fake.address(),
        "company_phone": get_random_no_hp(),
        "company_email": fake.email(),
        "invoice_number": _certificate_number("invoice"),
        "invoice_date": fake.date(pattern="%d-%m-%Y", end_datetime="-1d"),
        "due_date": fake.date(pattern="%d-%m-%Y", end_datetime="-1d"),
        "payment_terms": fake.sentence(),
        "client_name": fake.name(),
        "client_address": fake.address(),
        "client_phone": get_random_no_hp(),
        "project_name": fake.word(),
        "po_number": fake.random_int(min=100000, max=999999),
        "salesperson": fake.name(),
        "i_1_desc": fake.sentence(nb_words=6),
        "i_1_quantity": item_1_quantity,
        "i_1_rate": _rupiah_format(item_1_rate),
        "i_1_sum": _rupiah_format(item_1_amount),
        "i_1_tax": _rupiah_format(item_1_tax),
        "i_2_desc": fake.sentence(nb_words=6),
        "i_2_quantity": item_2_quantity,
        "i_2_rate": _rupiah_format(item_2_rate),
        "i_2_sum": _rupiah_format(item_2_amount),
        "i_2_tax": _rupiah_format(item_2_tax),
        "i_3_desc": fake.sentence(nb_words=6),
        "i_3_quantity": item_3_quantity,
        "i_3_rate": _rupiah_format(item_3_rate),
        "i_3_sum": _rupiah_format(item_3_amount),
        "i_3_tax": _rupiah_format(item_3_tax),
        "i_4_desc": fake.sentence(nb_words=6),
        "i_4_quantity": item_4_quantity,
        "i_4_rate": _rupiah_format(item_4_rate),
        "i_4_sum": _rupiah_format(item_4_amount),
        "i_4_tax": _rupiah_format(item_4_tax),
        "total_sum": _rupiah_format(total_amount),
        "total_tax": _rupiah_format(total_tax),
        "total": _rupiah_format(total),
        "bank_name": fake.random_element(
            elements=("BNI", "BRI", "BCA", "MANDIRI", "BNI", "BRI", "BCA", "MANDIRI")
        ),
        "account_number": fake.random_int(min=1000000000, max=9999999999),
        "account_name": fake.name(),
        "invoice_notes": fake.sentence(),
    }


def _job_application_template_values():
    from faker import Faker

    fake = Faker("id_ID")
    id = uuid.uuid4()
    gender = fake.random_element(elements=("Laki-Laki", "Perempuan"))
    marital_status = fake.random_element(
        elements=("Kawin", "Belum Kawin", "Pernah Kawin")
    )
    application_date = fake.date_between(start_date="-60w", end_date="today")
    start_date = application_date + timedelta(days=30)
    age = fake.random_int(min=24, max=40)
    dob = fake.date_of_birth(minimum_age=age, maximum_age=age)

    sd_year = fake.date_of_birth(minimum_age=age - 7, maximum_age=age - 7).strftime(
        "%Y"
    )
    smp_year = fake.date_of_birth(minimum_age=age - 13, maximum_age=age - 13).strftime(
        "%Y"
    )
    sma_year = fake.date_of_birth(minimum_age=age - 16, maximum_age=age - 16).strftime(
        "%Y"
    )

    last_jenjang = fake.random_element(
        elements=("D1", "D1", "S1", "S1", "S1", "S1", "S2")
    )

    if last_jenjang == "S1":
        age_lulus = age - fake.random_int(min=20, max=21)
    elif last_jenjang == "S2":
        age_lulus = age - fake.random_int(min=22, max=23)
    else:
        age_lulus = age - fake.random_int(min=17, max=19)

    last_year = fake.date_of_birth(
        minimum_age=age_lulus, maximum_age=age_lulus
    ).strftime("%Y")

    full_name = fake.name_male() if gender == "Laki-Laki" else fake.name_female()
    kabupaten = get_random_kabupaten_name()

    return {
        "nik": get_nik(gender, dob),
        "nama": full_name,
        "tempat_lahir": kabupaten.title(),
        "tanggal_lahir": dob.strftime("%d-%m-%Y"),
        "status_kawin": marital_status,
        "alamat": fake.street_address() + ", " + kabupaten.title(),
        "no_hp": get_random_no_hp(),
        "email": fake.email(),
        "sd_nama": f"{fake.random_element(elements=("SD", "SDN", "SDIT"))} {fake.random_int(min=1, max=100)} {kabupaten.title()}",
        "sd_tahun": sd_year,
        "smp_nama": f"{fake.random_element(elements=("SMP", "SMPN", "MTS"))} {fake.random_int(min=1, max=100)} {kabupaten.title()}",
        "smp_tahun": smp_year,
        "sma_nama": f"{fake.random_element(elements=("SMA", "SMK", "SMAN", "MA", "MAN"))} {fake.random_int(min=1, max=100)} {kabupaten.title()}",
        "sma_tahun": sma_year,
        "terakhir_jenjang": last_jenjang,
        "terakhir_institusi": fake.random_element(
            elements=("UIN", "Universitas Negeri", "Politeknik", "STMIK")
        )
        + " "
        + get_random_kabupaten_name(),
        "terakhir_jurusan": fake.random_element(
            elements=(
                "Teknik Informatika",
                "Sistem Informasi",
                "Robotika",
                "Desain Grafis",
                "Multimedia",
            )
        ),
        "terakhir_tahun": last_year,
        "kerja_perusahaan": fake.company(),
        "kerja_posisi": fake.job(),
        "kerja_periode": f"{fake.random_int(min=11, max=40)}",
        "kerja_gaji": _rupiah_format(fake.random_int(1000000, 5000000)),
        "kerja_alasan": fake.text(),
        "applied_posisi": fake.job(),
        "expected_salary": _rupiah_format(fake.random_int(5000000, 10000000)),
        "start_date": start_date.strftime("%d-%m-%Y"),
        "application_place": kabupaten.title(),
        "application_date": application_date.strftime("%d-%m-%Y"),
    }


def _medical_form_template_values():
    from faker import Faker

    fake = Faker("id_ID")
    id = uuid.uuid4()
    gender = fake.random_element(elements=("Laki-Laki", "Perempuan"))
    age = fake.random_int(min=18, max=70)
    dob = fake.date_of_birth(minimum_age=age, maximum_age=age)
    exam_date = fake.date_between(start_date="-60w", end_date="today")
    follow_up_date = exam_date + timedelta(days=7)

    return {
        "patient_name": (
            fake.name_male() if gender == "Laki-Laki" else fake.name_female()
        ),
        "patient_birth_date": dob.strftime("%d-%m-%Y"),
        "patient_age": age,
        "patient_gender": gender,
        "patient_address": fake.address(),
        "patient_phone": get_random_no_hp(),
        "patient_occupation": fake.job(),
        "insurance_number": _certificate_number("medical_form"),
        "exam_date": exam_date.strftime("%d-%m-%Y"),
        "doctor_name": fake.name(),
        "chief_complaint": fake.text(),
        "medical_history": fake.text(),
        "blood_pressure": f"{fake.random_int(min=100, max=200)} mmHg",
        "height": f"{fake.random_int(min=150, max=200)} cm",
        "weight": f"{fake.random_int(min=50, max=100)} kg",
        "temperature": f"{fake.random_int(min=36, max=37)}°C",
        "pulse_rate": f"{fake.random_int(min=60, max=100)} bpm",
        "diagnosis": fake.text(),
        "prescription": fake.text(),
        "recommendations": fake.text(),
        "follow_up_date": follow_up_date.strftime("%d-%m-%Y"),
        "clinic_location": get_random_kabupaten_name().title(),
    }


if __name__ == "__main__":
    app()
