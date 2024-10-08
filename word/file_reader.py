from script import Runtime
from pathlib import Path
from zipfile import ZipFile
from re import finditer
from enum import IntEnum
from datetime import datetime, date


class CellName(IntEnum):
    """Access to cells with data of interest"""

    PatientName = 0
    BirthDate = 1
    Address = 4
    Occupation = 8
    Doctor = 19
    Therapist = 20
    Admission = 23
    Discharge = 25
    Allergies = 31
    PainDiagnoses = 36
    MisuseDiagnoses = 39
    PsychiatricDiagnoses = 42
    OtherDiagnoses = 45
    CurrentAcuteMedication = 51
    CurrentBaseMedication = 52
    CurrentOtherMedication = 55
    FormerAcuteMedication = 58
    FormerBaseMedication = 59


def extract_text(content: str) -> list[str]:
    """Read all <w:t> elements within a paragraph tag, read the content and join it."""
    return [
        "".join([
            t.group(1) for t in finditer(r"<w:t(?:\s[^>]+)?>(.*?)</w:t>", p.group(1))
        ]) for p in finditer(r"<w:p(?:\s[^>]+)?>(.*?)</w:p>", content)
    ]


def parse_medication(runtime: Runtime, text: list[str], medication_type: CellName):
    for med_entry in list(
            zip(
                ["name", "dosage", "unit", "morning", "noon", "evening", "night"],
                *[m.group(*list(range(1, 8)))
                  for m in finditer(
                        r"([äüöÄÜÖß0-9\w\- ]+?)\s+([\d.,/\-?]+)\s*(\S+)"
                        r"(?:\s+([\d.,/?]+)\s*-\s*([\d.,/?]+)\s*-\s*([\d.,/?]+)"
                        r"(?:\s*-\s*([\d.,/?]+))?)?", "\n".join(text))]
            )
    ):
        runtime.namespaces[
            f"medication:current:"
            f"{'base' if medication_type == CellName.CurrentBaseMedication else 'other'}:"
            f"{med_entry[0]}"] = list(map(lambda x: 0 if x is None else x, med_entry[1:]))

        if medication_type == CellName.CurrentBaseMedication and med_entry[0] == "name":
            runtime.namespaces["medication:former:base"].extend(med_entry[1:])


def attach_runtime(runtime: Runtime, file_name: Path):
    with ZipFile(file_name, "r") as zip_archive:
        content: str = zip_archive.read("word/document.xml").decode("utf-8")

    runtime.namespaces["diagnoses:icd10"] = []
    runtime.namespaces["diagnoses:names"] = []
    runtime.namespaces["medication:former:base"] = []
    runtime.namespaces["medication:former:acute"] = []

    for i, cell in enumerate(finditer(r"<w:tc(?:\s[^>]+)?>(.*?)</w:tc>", content)):
        if i not in CellName:
            continue

        text: list[str] = extract_text(cell.group(1))
        match i:
            case CellName.PatientName:
                runtime.namespaces["patient:last_name"], runtime.namespaces["patient:first_name"] = \
                    list(map(str.strip, text[0].split(",")))[0:2]

            case CellName.BirthDate:
                birthdate: date = datetime.strptime(text[0], "%d.%m.%Y").date()
                today: date = date.today()
                runtime.namespaces["patient:birthdate"] = text[0]
                runtime.namespaces["patient:age"] = (today.year - birthdate.year -
                                                     ((today.month, today.day) < (birthdate.month, birthdate.day)))

            case CellName.Address:
                runtime.namespaces["patient:address"] = text[0]

            case CellName.Occupation:
                runtime.namespaces["patient:occupation"] = text[0]

            case CellName.Doctor:
                runtime.namespaces["patient:doctor"] = text[0].removeprefix("Arzt: ")

            case CellName.Therapist:
                runtime.namespaces["patient:therapist"] = text[0].removeprefix("Psych.: ")

            case CellName.Admission:
                runtime.namespaces["patient:admission"] = text[0]

            case CellName.Discharge:
                runtime.namespaces["patient:discharge"] = text[0]

            case CellName.Allergies:
                runtime.namespaces["patient:allergies"] = ", ".join(text)

            case (CellName.PainDiagnoses |
                  CellName.MisuseDiagnoses |
                  CellName.PsychiatricDiagnoses |
                  CellName.OtherDiagnoses):

                diagnoses: list[tuple[str, str]] = list(zip(*[
                    (m.group(2), m.group(1).strip())
                    for m in finditer(r"([äöüÄÖÜß\w\-,. ]+)([A-Z]\d{2,3}(?:\.\d{1,3})?)", "\n".join(text))
                ]))

                if diagnoses:
                    runtime.namespaces["diagnoses:icd10"].extend(diagnoses[0])
                    runtime.namespaces["diagnoses:names"].extend(diagnoses[1])

            case (CellName.CurrentAcuteMedication |
                  CellName.FormerAcuteMedication |
                  CellName.FormerBaseMedication):

                if i == CellName.FormerBaseMedication:
                    med_field_name: str = "medication:former:base"
                else:
                    med_field_name: str = "medication:former:acute"

                runtime.namespaces[med_field_name].extend([
                    med_name.strip() for med_name in ",".join(text[1:]).split(",") if med_name
                ])

            case CellName.CurrentBaseMedication | CellName.CurrentOtherMedication:
                parse_medication(runtime, text, CellName(i))

