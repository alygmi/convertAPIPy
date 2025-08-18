from fastapi.responses import JSONResponse


def ok_json(data):
    return JSONResponse(status_code=200, content=data)


def bad_request_json(data):
    return JSONResponse(status_code=400, content=data)


def br_failed(ts, code, message):
    return JSONResponse(status_code=400, content={
        "timestamp": ts,
        "code": code,
        "message": message
    })


def assess_error(errors_list: list):
    """
    Mengembalikan error pertama yang ditemukan dalam list,
    atau None kalau semua None.
    """
    for err in errors_list:
        if err is not None:
            return err
    return None
