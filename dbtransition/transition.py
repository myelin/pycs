# controller for data export / import

def main():
    src_tag = 'mk'
    dest_tag = 'postgres'

    src_mod = __import__("export_from_%s" % src_tag)
    dest_mod = __import__("import_to_%s" % dest_tag)

    writer = dest_mod.writer("/home/pycs/dbdump.sql")
    src_mod.export(writer)

if __name__ == '__main__':
    main()
