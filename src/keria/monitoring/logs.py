import logging


class TruncatedFormatter(logging.Formatter):
    """Formats log records with shorter module and function names and a right justified line number for readability."""

    def __init__(self, fmt=None, datefmt=None, style="%"):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        # Truncate module and funcName to first 'chars' characters
        mod_chars = 12  # number of spaces to truncate to
        fn_chars = 16  # number of spaces to truncate to
        record.module = (record.module[:mod_chars] + " " * mod_chars)[:mod_chars]
        record.funcName = (record.funcName[:fn_chars] + " " * fn_chars)[:fn_chars]
        record.lineno = str(record.lineno).rjust(
            5
        )  # Ensure line number is right-aligned
        try:
            return super().format(record)
        except Exception as e:
            logging.error(f"Error formatting log record: {e}")
            raise e
