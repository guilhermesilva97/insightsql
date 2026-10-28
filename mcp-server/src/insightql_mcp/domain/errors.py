class InsightError(Exception):
    pass


class QueryRejected(InsightError):
    pass


class TableNotFound(InsightError):
    pass
