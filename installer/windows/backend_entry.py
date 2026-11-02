"""Console backend packaged separately so QProcess receives JSONL output."""
import sys

if __name__ == '__main__':
    if sys.argv[1:2] == ['--protocol-test']:
        from worker import emit
        emit('progress', 'Verifying localized path: Syna 🐱', progress=10)
        emit('done', 'Installation complete, verification passed.', progress=100)
    elif sys.argv[1:2] == ['--esptool']:
        sys.argv.pop(1)
        import esptool
        esptool._main()
    else:
        from worker import main, emit
        try:
            main()
        except Exception as error:
            emit('error', str(error))
            sys.exit(1)
