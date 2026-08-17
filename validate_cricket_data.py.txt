from pathlib import Path
import yaml

DATA_PATH = Path(
    r"C:\Users\HP\.gemini\antigravity\scratch\cricketgpt\Archive\criket-data"
)

yaml_files = list(DATA_PATH.rglob("*.yaml"))

print("=" * 60)
print("CRICKET DATA VALIDATION")
print("=" * 60)

print(f"YAML files found: {len(yaml_files)}")

successful = 0
failed = 0
failed_files = []

for i, file_path in enumerate(yaml_files, 1):

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if data is None:
            failed += 1
            failed_files.append((str(file_path), "Empty YAML"))
        else:
            successful += 1

    except Exception as e:
        failed += 1
        failed_files.append((str(file_path), str(e)))

    if i % 1000 == 0:
        print(f"Checked {i}/{len(yaml_files)} files...")

print()
print("=" * 60)
print("RESULT")
print("=" * 60)

print(f"YAML files found:       {len(yaml_files)}")
print(f"Successfully read:      {successful}")
print(f"Failed:                 {failed}")
print(f"Total checked:          {successful + failed}")

if failed_files:
    print("\nFAILED FILES:")

    for file_path, error in failed_files:
        print(f"\n{file_path}")
        print(f"Error: {error}")
else:
    print("\nALL YAML FILES READ SUCCESSFULLY!")