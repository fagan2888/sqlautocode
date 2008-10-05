import optparse, os, sys

options = None
out = sys.stdout
err = sys.stderr
dburl  = None
engine = None

# TODO: encoding (default utf-8)

def create_parser():
    parser = optparse.OptionParser(
        """autocode.py <database_url> [options, ]
Generates Python source code for a given database schema.

Example: ./autocode.py postgres://user:password@myhost/database -o out.py""")

    parser.add_option(
        "-o", "--output",
        help="Write to file (default is stdout)",
        action="store", dest="output")

    parser.add_option(
        "--force",
        help="Overwrite Write to file (default is stdout)",
        action="store_true", dest="force")

    parser.add_option(
        "-s", "--schema",
        help="Optional, reflect a non-default schema",
        action="store", dest="schema")

    parser.add_option(
        "-t", "--tables",
        help=("Optional, only reflect this comma-separated list of tables. "
              "Wildcarding with '*' is supported, e.g: --tables account_*,"
              "orders,order_items,*_audit"),
        action="callback", callback=_prep_tables, type="string", dest="tables")

    parser.add_option(
        "-i", "--noindexes", "--noindex",
        help="Do not emit index information",
        action="store_true", dest="noindex")

    parser.add_option(
        "-g", "--generic-types",
        help="Emit generic ANSI column types instead of database-specific.",
        action="store_true", dest="generictypes")

    parser.add_option(
        "--encoding",
        help="Encoding for output, default utf8",
        action="store", dest="encoding")

    parser.add_option(
        "-e", "--example",
        help="Generate code with examples how to access data",
        action="store_true", dest="example")

    parser.add_option(
        "-3", "--z3c",
        help="Generate code for use with z3c.sqlalchemy",
        action="store_true", dest="z3c")

    parser.set_defaults(tables=[],
                        encoding='utf8')
    return parser

def _prep_tables(option, opt_str, value, parser):
    if not value:
        parser.values.tables = []
    else:
        parser.values.tables = [x.strip()
                                for x in value.split(',')
                                if x.strip() != '']

def _version_check(parser):
    try:
        import sqlalchemy
    except ImportError, ex:
        parser.error("SQLAlchemy version 0.4.0 or higher is required. (%s)" %
                     (ex))

    version = getattr(sqlalchemy, '__version__', None)
    if version is None:
        parser.error("SQLAlchemy version 0.4.0 or higher is required.")
    elif version == 'svn':
        pass
    else:
        try:
            version_info = tuple([int(i) for i in version.split('.')[:2]])
            if version_info < (0, 4):
                parser.error("SQLAlchemy version 0.4.0 or higher is required.")
        except ValueError:
            # some versions need some relaxed check
            print >>err, 'Warning: Could not recognize version %s - please make sure that youre using 0.4.x' % version
            pass

def _setup_engine(parser, url):
    global engine

    import sqlalchemy
    try:
        engine = sqlalchemy.create_engine(url)
        test = engine.connect()
        test.close()
    except sqlalchemy.exceptions.SQLAlchemyError, ex:
        parser.error('Could not connect to "%s": %s' % (url, ex))


def _instrument():
    # monkeypatch SQLAlchemy __repr__ methods
    import formatter
    import loader

def _set_output(path, overwrite=False):
    if os.path.exists(path) and not overwrite:
        print >>err, 'File "%s" exists and will be overwritten.' % path
        resp = raw_input('Overwrite (y/[n]): ')
        if not resp.strip().lower().startswith('y'):
            print >>err, "Aborted."
            sys.exit(-1)

    global out
    try:
        out = open(path, 'w')
    except IOError, e:
        print >>err, 'Could not open "%s" for writing: %s' % (path, e)
        sys.exit(-1)


def configure(argv=sys.argv):
    global options, dburl

    parser = create_parser()
    options, args = parser.parse_args(argv)

    if len(args) < 2:
        parser.error("A database URL is required.")
    elif len(args) > 2:
        parser.error("Unknown arguments: %s" % (' '.join(args[2:])))
    else:
        dburl = args[1]

    _version_check(parser)

    _setup_engine(parser, dburl)

    _instrument()
    
    if options.output is not None:
        _set_output(options.output, options.force)
