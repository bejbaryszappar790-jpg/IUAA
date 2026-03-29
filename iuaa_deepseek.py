from ai_modules.file_reader import read_file
from ai_modules.evaluator import evaluate_candidate

FILE_PATH = "/home/kharun/Downloads/New_Document.docx"

def main():
    text = read_file(FILE_PATH)
    result = evaluate_candidate(text)
    print(result)

if __name__ == "__main__":
    main()