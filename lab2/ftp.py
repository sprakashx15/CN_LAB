from ftplib import FTP
import os

# FTP server details (change according to your setup)
FTP_HOST = "ftp.dlptest.com"     # public test FTP server
FTP_USER = "dlpuser"             # demo username
FTP_PASS = "rNrKYTX9g7z3RgJRmxWuGHbeu"  # demo password

def main():
    # Connect to FTP server
    ftp = FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    print("Successfuly Connected to FTP server")

    print("\n Directory listing:")
    ftp.retrlines("LIST")

    # Upload a file
    filename = "test.txt"
    with open(filename, "w") as f:
        f.write("This is a test file for FTP upload. And later will be downloaded.\n")

    with open(filename, "rb") as f:
        ftp.storbinary(f"STOR {filename}", f)
    print(f"\n Uploaded file: {filename}")

    print("\n Directory listing after upload:")
    ftp.retrlines("LIST")

    # Download the same file
    downloaded_file = "downloaded_" + filename
    with open(downloaded_file, "wb") as f:
        ftp.retrbinary(f"RETR {filename}", f.write)
    print(f"\n Downloaded file: {downloaded_file}")

    with open(downloaded_file, "r") as f:
        content = f.read()
    print("\ Downloaded file content:")
    print(content)

    ftp.quit()
    print("\n FTP connection closed")

if __name__ == "__main__":
    main()
