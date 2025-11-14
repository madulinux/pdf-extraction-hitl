from datetime import datetime
import random
import os
import json
from typing import List


def get_nik(
    gender: str = "Laki-Laki",
    date_of_birth: datetime = None,
    kabupaten_id: str = None,
    kecamatan_id: str = None,
):
    from faker import Faker

    fake = Faker("id_ID")
    dob = (
        fake.date_of_birth(minimum_age=18, maximum_age=65)
        if date_of_birth == None
        else date_of_birth
    )

    if kabupaten_id and len(kabupaten_id) == 6:
        if kecamatan_id and len(kecamatan_id) == 6:
            pass
        else:
            kecamatan = get_kecamatan(kabupaten_id)
            kecamatan_id = kecamatan.get("id")

    if kecamatan_id == None or len(kecamatan_id) < 6:
        kecamatan = get_kecamatan()
        kecamatan_id = kecamatan.get("id")

    dob_day = (
        dob.strftime("%d") if gender == "Laki-Laki" else int(dob.strftime("%d")) + 40
    )
    dob_month = dob.strftime("%m")
    dob_year = dob.strftime("%y")

    # random int 1 - 9 padded with 0
    last_4 = str(random.randint(1, 9)).zfill(4)

    return f"{kecamatan_id}{dob_year}{dob_month}{dob_day}{last_4}"


def get_provinsis() -> List[dict]:
    provinsis_json = os.path.join(os.getcwd(), "storage/data/provinsis.json")
    with open(provinsis_json, "r") as f:
        provinsis = json.load(f)

    return provinsis


def get_kabupatens(provinsi_id: str = None) -> List[dict]:
    kabupatens_json = os.path.join(os.getcwd(), "storage/data/kabupatens.json")
    result = []
    with open(kabupatens_json, "r") as f:
        kabupatens = json.load(f)
        if provinsi_id:
            result = [k for k in kabupatens if k.get("provinsi_id") == provinsi_id]
        else:
            result = kabupatens
    return result


def get_kecamatans(kabupaten_id: str = None) -> List[dict]:
    kecamatans_json = os.path.join(os.getcwd(), "storage/data/kecamatans.json")
    result = []
    with open(kecamatans_json, "r") as f:
        kecamatans = json.load(f)
        if kabupaten_id:
            result = [k for k in kecamatans if k.get("kabupaten_id") == kabupaten_id]
        else:
            result = kecamatans
    return result


def get_kelurahans(kecamatan_id: str = None) -> List[dict]:
    kelurahans_json = os.path.join(os.getcwd(), "storage/data/kelurahans.json")
    result = []
    with open(kelurahans_json, "r") as f:
        kelurahans = json.load(f)
        if kecamatan_id:
            result = [k for k in kelurahans if k.get("kecamatan_id") == kecamatan_id]
        else:
            result = kelurahans
    return result


def get_provinsi(id: str = None) -> str:
    provinsis = get_provinsis()

    if id == None:
        # return random key
        return random.choice(provinsis)
    else:
        res = [k for k in provinsis if k.get("id") == id]
        return random.choice(res) if res else None


def get_kabupaten(id: str = None, provinsi_id: str = None) -> dict:
    kabupatens = get_kabupatens(provinsi_id)
    if id:
        # return kabupaten where kabupaten.id = id
        res = [k for k in kabupatens if k.get("id") == id]
        return random.choice(res) if res else None
    else:
        # return random kabupaten
        return random.choice(kabupatens)


def get_kecamatan(id: str = None, kabupaten_id: str = None) -> dict:
    kecamatans = get_kecamatans(kabupaten_id)
    if id:
        # return kecamatan where kecamatan.id = id
        res = [k for k in kecamatans if k.get("id") == id]
        return random.choice(res) if res else None
    else:
        # return random kecamatan
        return random.choice(kecamatans)


def get_kelurahan(id: str = None, kecamatan_id: str = None) -> dict:
    kelurahans = get_kelurahans(kecamatan_id)
    if id:
        # return kelurahan where kelurahan.id = id
        res = [k for k in kelurahans if k.get("id") == id]
        return random.choice(res) if res else None
    else:
        # return random kelurahan
        return random.choice(kelurahans)


def get_random_no_hp() -> str:
    return f"08{random.randint(1, 99):02d}{random.randint(0, 99):02d}{random.randint(0, 99):02d}{random.randint(0, 99):02d}"


def test():
    print(get_kelurahan())


if __name__ == "__main__":
    test()
