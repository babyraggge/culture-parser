from Parser import Parser


def main():
    p = Parser()
    p.parse('test.csv', region='sverdlovskaya-oblast', tag="Бесплатно", start="2022-04-22", end="2022-04-22")


if __name__ == '__main__':
    main()
