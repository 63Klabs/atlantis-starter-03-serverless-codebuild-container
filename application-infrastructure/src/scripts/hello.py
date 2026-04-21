# python3

def main():
    horizontal_line = r"""
-------------------------------------------------------------------------
    """
    hello_world = r"""
 _   _  _____ _     _      ___        __        _____  ____  _     ____
| | | || ____| |   | |    / _ \       \ \      / / _ \|  _ \| |   |  _ \
| |_| ||  _| | |   | |   | | | |       \ \ /\ / / | | | |_) | |   | | | |
|  _  || |___| |___| |___| |_| |  _     \ V  V /| |_| |  _ <| |___| |_| |
|_| |_||_____|_____|_____|\___/  ( )     \_/\_/  \___/|_| \_\_____|____/
                                 |/
    """

    about = r"""
Hello, World!
This is a scheduled job using CodeBuild
Deployed using the 63Klabs Atlantis Template and Scripts Platform
    """

    print(horizontal_line)
    print(hello_world)
    print(about)
    print(horizontal_line)

if __name__ == "__main__":
    main()
