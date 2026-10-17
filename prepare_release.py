"""Generate Windows version metadata from the single VERSION file."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def read_version():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    match = VERSION_PATTERN.fullmatch(version)
    if not match:
        raise SystemExit("VERSION must contain a semantic version such as 1.1.0")
    return version, tuple(int(part) for part in match.groups())


def main():
    version, (major, minor, patch) = read_version()
    numeric = f"({major}, {minor}, {patch}, 0)"
    contents = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={numeric}, prodvers={numeric}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Prajwala Adiga'),
      StringStruct('FileDescription', 'Fahadh Water Companion'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'FahadhWaterCompanion'),
      StringStruct('OriginalFilename', 'FahadhWaterCompanion.exe'),
      StringStruct('ProductName', 'Fahadh Water Companion'),
      StringStruct('ProductVersion', '{version}')
    ])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    (ROOT / "version_info.txt").write_text(contents, encoding="utf-8", newline="\n")
    print(version)


if __name__ == "__main__":
    main()
