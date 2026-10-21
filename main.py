from datetime import datetime


def main():
    now = datetime.now()
    print(f"Today's date: {now:%A, %B %d, %Y}")
    print(f"Current time: {now:%I:%M:%S %p}")


if __name__ == "__main__":
    main()
