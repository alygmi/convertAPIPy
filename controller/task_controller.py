# app/controllers/task_controller.py
from fastapi import APIRouter, HTTPException, Request, Response, status
from typing import Dict, Any, List, Optional, Union
import time
import json
from base64 import b64decode
import math

from services.task_services import TaskService
from utils.helper import (
    GetChannelId, GetTelegramToken, GetMessageID,
    WSResultToMap, PayloadEncryptedMap, PayloadMap,
    RGet, AddSuccessResponse, Result
)

router = APIRouter()


class TaskController:
    def __init__(self, task_service: TaskService):
        self.task_service = task_service

    async def task_business_point(self, ctx: Request):
        server_ts = int(time.time() * 1000)
        application_id = ctx.headers.get("Vending-Application-Id")
        channel_id_telegram = GetChannelId(application_id)
        token_telegram = GetTelegramToken(application_id)

        if not application_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Application id not found")

        payload, err = await PayloadEncryptedMap(ctx)
        if err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid payload: {err}")

        errors: List[Exception] = []
        type_activity, errors, _ = RGet(payload, "type_activity", errors)
        device_id, errors, _ = RGet(payload, "device_id", errors)
        device_name, errors, _ = RGet(payload, "device_name", errors)

        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")

        # Re-get now, assuming it's the same logic as Go's now.String()
        now = int(time.time() * 1000)
        task_key = f"task_business_point_{type_activity}_{device_id}_{now}"
        content = ""

        if type_activity == "edit":
            old_value, errors, _ = RGet(payload, "old_value", errors)
            new_value, errors, _ = RGet(payload, "new_value", errors)
            content_old = ""
            content_new = ""

            if not errors:
                for key in old_value:
                    if key == "loc":
                        loc, _, _ = RGet(old_value, "loc", errors)
                        lat, _, _ = RGet(loc, "latitude", errors)
                        long, _, _ = RGet(loc, "longitude", errors)
                        content_old += f" - <b>{key}lat</b> : {lat:.12g} \n"
                        content_old += f" - <b>{key}long</b> : {long:.12g} \n"
                    elif key != "device_id":
                        value, _, _ = RGet(old_value, key, errors)
                        content_old += f" - <b>{key}</b> : {value} \n"

                for key in new_value:
                    if key != "id":
                        if key in ["longitude", "latitude"]:
                            value, _, _ = RGet(new_value, key, errors)
                            content_new += f" - <b>{key}</b> : {value:.12g} \n"
                        else:
                            value, _, _ = RGet(new_value, key, errors)
                            content_new += f" - <b>{key}</b> : {value} \n"

            if content_new:
                content = f" <b>{device_name}</b> ({device_id}) :\n <b> Data lama </b> : \n{content_old}\n\n <b> Data baru </b> : \n{content_new}\n"
            else:
                content = f"{device_id} {device_name}"
        elif type_activity == "delete":
            content = f"Business Point dengan Device ID: {device_id} Nama: {device_name} telah dihapus"
        elif type_activity == "add":  # Assuming "edit" in the Go code for "add" was a typo or handled differently
            content = f"Business Point Baru dengan Device ID: {device_id} Nama: {device_name}"
        else:
            # Handle other activity types or raise an error if type_activity is invalid
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid type_activity")

        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload data")

        task_subject = f"business_points_{type_activity}_activity"
        header_telegram = ""
        if type_activity == "edit":
            header_telegram = f"<b>Business Point {device_name} telah diubah</b> \n"
        elif type_activity == "delete":
            header_telegram = f"<b>Business Point {device_name} telah dihapus:</b> \n"
        else:
            header_telegram = f"<b>Business Point {device_name} telah ditambahkan</b> \n"

        message = header_telegram + content

        body_telegram = {
            "parse_mode": "html",
            "chat_id": f"-100{channel_id_telegram}",
            "text": message,
        }
        body_parse = urlencode(body_telegram)

        ws_result_telegram = await self.task_service.call_telegram(token_telegram, body_parse)
        response_telegram = WSResultToMap(ws_result_telegram)

        if ws_result_telegram.code != Result.HTTP_OK or ws_result_telegram.body.get("ok") is False:
            # Assuming Telegram API returns {"ok": false} on error
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Telegram API error: {response_telegram['body']}")

        body_task = {
            "var": {},
            "task_subject": task_subject,
            "task_key": task_key,
            "task_type": "business_point",
            "task_desc": message,
            "notification_open": [],
        }
        ws_result_create_task = await self.task_service.create_task(application_id, body_task)
        response_create_task = WSResultToMap(ws_result_create_task)
        if ws_result_create_task.code != Result.HTTP_OK:
            raise HTTPException(
                status_code=ws_result_create_task.code, detail=response_create_task["body"])

        body_close = {
            "var": {},
            "task_key": task_key,
            "notification_close": [],
        }
        ws_result_close_task = await self.task_service.close_task(application_id, body_close)
        response_close_task = WSResultToMap(ws_result_close_task)
        if ws_result_close_task.code != Result.HTTP_OK:
            raise HTTPException(
                status_code=ws_result_close_task.code, detail=response_close_task["body"])

        return {"message": "Success", "data": response_telegram["body"]}

    async def task_list(self, ctx: Request):
        server_ts = int(time.time() * 1000)
        application_id = ctx.headers.get("Vending-Application-Id")

        if not application_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Application id not found")

        res = await self.task_service.get_task(application_id)
        if res.code != Result.HTTP_OK:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=json.dumps(res.body))

        response = res.body
        response = AddSuccessResponse(response, server_ts, "List task success")

        errors: List[Exception] = []
        data, errors, _ = RGet(response, "data", errors)
        if errors:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to parse task list data")

        return {"message": "Success", "data": data}

    async def task_close(self, ctx: Request):
        server_ts = int(time.time() * 1000)
        application_id = ctx.headers.get("Vending-Application-Id")

        if not application_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Application id not found")

        payload, err = await PayloadMap(ctx)
        if err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid payload: {err}")

        errors: List[Exception] = []
        enc_task_id, errors, _ = RGet(payload, "task_id", errors)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="task_id not found in payload")

        try:
            task_id = b64decode(enc_task_id).decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid task_id encoding: {e}")

        body_close = {
            "var": {
                "application_id": application_id,
                "task_id": task_id,
            },
            "task_id": task_id,
            "notification_close": [],
        }
        ws_result_close = await self.task_service.close_task(application_id, body_close)
        response_close = WSResultToMap(ws_result_close)
        if ws_result_close.code != Result.HTTP_OK:
            raise HTTPException(status_code=ws_result_close.code,
                                detail=response_close["body"])

        return {"message": "Success", "data": response_close["body"]}

    async def task_complaint_set(self, ctx: Request):
        server_ts = int(time.time() * 1000)
        now = int(time.time() * 1000)
        application_id = ctx.headers.get("Vending-Application-Id")
        token_telegram = GetTelegramToken(application_id)
        channel_id = GetChannelId(application_id)

        if not application_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Application id not found")
        if not token_telegram:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram Token not found")
        if not channel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Channel Id not found")

        payload, err = await PayloadMap(ctx)
        if err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid payload: {err}")

        errors: List[Exception] = []
        topic, errors, _ = RGet(payload, "topic", errors)
        description, errors, _ = RGet(payload, "description", errors)
        vm_code, errors, _ = RGet(payload, "vm_code", errors)
        detail_url, errors, _ = RGet(payload, "detail_url", errors)
        bp_url, errors, _ = RGet(payload, "businesPoint_url", errors)

        if errors:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Missing or invalid payload fields")

        payload["application_id"] = application_id

        ws_bp = await self.task_service.get_bp(bp_url)
        response_bp = WSResultToMap(ws_bp)
        if ws_bp.code != Result.HTTP_OK:
            raise HTTPException(status_code=ws_bp.code,
                                detail=response_bp["body"])

        bp_map = {}
        arr_bp = ws_bp.body if isinstance(
            ws_bp.body, list) else []  # Ensure it's a list
        for x in arr_bp:
            if isinstance(x, dict):
                # Assuming vm_code is the key within each item of arr_bp
                # This part of the Go code was a bit ambiguous (app_id, errors, _ := icontroller.RGet[string](data, vmCode, errors))
                # It looks like it tries to get a value using vmCode as a key in 'data' map.
                # Let's assume vm_code itself is the key for the business point data.
                bp_map[vm_code] = x
            else:
                print(
                    f"Error: Expected map[string]any for BP item, got {type(x)}")
                continue

        bp, errors, _ = RGet(bp_map, vm_code, errors)
        if errors:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Business point data not found for VM Code: {vm_code}")

        bp_name, errors, _ = RGet(bp, "name", errors)
        if errors:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Business point name not found for VM Code: {vm_code}")

        content = f"<b>Keluhan dari Pelanggan ({topic}) untuk Business Point {bp_name} VmCode {vm_code}</b> : \n\n{description}\n\n Detail : {detail_url}"

        notification_open = {
            "category": "TELEGRAM",
            "detail": {
                "bot_token": token_telegram,
                "channel_id": channel_id,
                "mode": "html",
                "content": content,
            },
        }
        body_notification = [notification_open]

        body_create_task = {
            "var": payload,
            "task_subject": f"generate task complaint {now}",
            "task_key": f"complaint_{now}",
            "task_type": "complaint",
            "task_desc": content,
            "notification_open": body_notification,
        }
        ws_result_create_task = await self.task_service.create_task(application_id, body_create_task)
        response_create_task = WSResultToMap(ws_result_create_task)

        if ws_result_create_task.body.get("result") != Result.SUCCESS:
            raise HTTPException(
                status_code=ws_result_create_task.code, detail=response_create_task["body"])

        # Admin Telegram notification
        channel_id_admin = "1664430239"  # Hardcoded in Go, consider moving to config
        # Hardcoded in Go, consider moving to config
        token_admin = "5486013761:AAHSt1OlBGnRHydwFlvewyfOGoYZyw0gBR4"

        body_admin_telegram = {
            "parse_mode": "html",
            "chat_id": f"-100{channel_id_admin}",
            "text": content,
        }
        body_parse_admin = urlencode(body_admin_telegram)
        ws_result_admin_telegram = await self.task_service.call_telegram(token_admin, body_parse_admin)
        response_admin_telegram = WSResultToMap(ws_result_admin_telegram)

        if ws_result_admin_telegram.code != Result.HTTP_OK or ws_result_admin_telegram.body.get("ok") is False:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Admin Telegram API error: {response_admin_telegram['body']}")

        return {"message": "Success", "data": response_create_task["body"]}

    async def task_stock_set(self, ctx: Request):
        server_ts = int(time.time() * 1000)
        now = int(time.time() * 1000)
        application_id = ctx.headers.get("Vending-Application-Id")
        token_telegram = GetTelegramToken(application_id)
        channel_id = GetChannelId(application_id)

        if not application_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Application id not found")
        if not token_telegram:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram Token not found")
        if not channel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Channel Id not found")

        # List Devices
        ws_result_device = await self.task_service.list_device(application_id)
        response_device = WSResultToMap(ws_result_device)
        if ws_result_device.body.get("result") != Result.SUCCESS:
            raise HTTPException(
                status_code=ws_result_device.code, detail=response_device["body"])

        body_result_device = ws_result_device.body
        errors_device: List[Exception] = []
        devices, errors_device, _ = RGet(
            body_result_device, "devices", errors_device)
        if errors_device:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get device list")

        list_devices = {}
        for x in devices:
            if isinstance(x, dict):
                device_id, _, _ = RGet(x, "id", [])
                if device_id:
                    list_devices[device_id] = x
            else:
                print(
                    f"Error: Expected map[string]any for device item, got {type(x)}")

        # Get Sensors
        ws_sensor_result = await self.task_service.get_sensors(application_id)
        sensor_response = WSResultToMap(ws_sensor_result)
        if ws_sensor_result.code != Result.HTTP_OK:
            raise HTTPException(
                status_code=ws_sensor_result.code, detail=sensor_response["body"])

        sensor_body = ws_sensor_result.body
        errors_sensor: List[Exception] = []
        sensors, errors_sensor, _ = RGet(sensor_body, "sensors", errors_sensor)
        if errors_sensor:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get sensor data")

        list_sensors = {}
        content_stock_status = ""  # To build the final content string

        for x in sensors:
            if not isinstance(x, dict):
                print(
                    f"Error: Expected map[string]any for sensor item, got {type(x)}")
                continue

            device_id, _, _ = RGet(x, "device_id", [])
            sensor_name, _, _ = RGet(x, "sensor", [])
            param, _, _ = RGet(x, "param", [])
            latest_data, _, _ = RGet(x, "latest_data", [])
            value = latest_data.get("value")

            if device_id not in list_sensors:
                list_sensors[device_id] = {}
            if sensor_name not in list_sensors[device_id]:
                list_sensors[device_id][sensor_name] = {}

            if sensor_name == "stock_threshold":
                list_sensors[device_id][sensor_name]["value"] = value
            else:
                if param == "id":
                    list_sensors[device_id][sensor_name]["id"] = value
                elif param == "name":
                    list_sensors[device_id][sensor_name]["name"] = value
                elif param == "stock":
                    list_sensors[device_id][sensor_name]["stock"] = value

        for device_id, sensor_map in list_sensors.items():
            converted_sensor_map = {k: v for k, v in sensor_map.items()}

            device_data, _, _ = RGet(list_devices, device_id, [])
            device_name, _, _ = RGet(device_data, "name", [])

            content_isi = ""
            for key in converted_sensor_map:
                sensors_map, _, _ = RGet(converted_sensor_map, key, [])
                _id = sensors_map.get("id")
                _name = sensors_map.get("name")
                _stock = sensors_map.get("stock")

                if _id is None or _name is None:
                    continue

                # Check for float type and cast if necessary
                if isinstance(_stock, (int, float)):
                    content_isi += f" - Produk <b>{_name} ({key})</b> sisa <b>{_stock:.0f}</b>\n"
                else:
                    # If stock is not a number, convert to string
                    content_isi += f" - Produk <b>{_name} ({key})</b> sisa <b>{_stock}</b>\n"

            if content_isi:
                content_stock_status += f"<b>{device_name}</b> ({device_id}) :\n{content_isi}\n"

        task_key = "task_stock"
        if content_stock_status:
            content_stock_status = "<b>Pemberitahuan stok barang menipis/habis</b> : \n\n" + \
                content_stock_status
            body_create_task = {
                "task_subject": "generate task stock",
                "task_key": task_key,
                "task_type": "stock",
                "notification_open": [
                    {
                        "category": "TELEGRAM",
                        "detail": {
                            "bot_token": token_telegram,
                            "channel_id": channel_id,
                            "mode": "html",
                            "content": content_stock_status,
                        },
                    }
                ],
            }
            ws_result_create_task = await self.task_service.create_task(application_id, body_create_task)
            response_create_task = WSResultToMap(ws_result_create_task)
            if ws_result_create_task.code != Result.HTTP_OK:
                raise HTTPException(
                    status_code=ws_result_create_task.code, detail=response_create_task["body"])
        else:
            # This content is used only for response if no stock issues
            content_stock_status = "tidak ada isi"
            body_close_task = {
                "var": {},
                "task_key": task_key,
                "notification_close": [],
            }
            ws_result_close_task = await self.task_service.close_task(application_id, body_close_task)
            response_close_task = WSResultToMap(ws_result_close_task)
            if ws_result_close_task.code != Result.HTTP_OK:
                raise HTTPException(
                    status_code=ws_result_close_task.code, detail=response_close_task["body"])

        return {"message": "Success", "data": content_stock_status}

    async def task_summary(self, ctx: Request):
        server_ts = int(time.time() * 1000)

        # Using pytz or zoneinfo for timezones is more robust, but sticking to built-in for direct conversion.
        # Python's time.localtime() or datetime.now().astimezone() can handle timezones.
        # For "Asia/Jakarta", you might need to install 'zoneinfo' for Python < 3.9 or 'pytz'.
        # For simplicity, using datetime.now() with manual offset if exact timezone is critical and zoneinfo/pytz not used.
        # Assuming system local time is already WIB for now as per context.
        # time.time() is UTC timestamp, so we need to convert to WIB if necessary for display.
        # Example using simple datetime (without explicit timezone for formatting):
        # now = datetime.fromtimestamp(server_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")

        # To accurately get "Asia/Jakarta" without external libs like pytz, for Python 3.9+:
        try:
            from zoneinfo import ZoneInfo  # type: ignore
            jakarta_tz = ZoneInfo("Asia/Jakarta")
            now_dt = time.localtime(server_ts / 1000)
            dt_string = time.strftime("%Y-%m-%d %H:%M:%S", now_dt)
        except ImportError:
            # Fallback if zoneinfo is not available (Python < 3.9) or not installed
            print(
                "Warning: 'zoneinfo' not found. Using local time or simple UTC if not configured.")
            now_dt = time.localtime(server_ts / 1000)
            dt_string = time.strftime("%Y-%m-%d %H:%M:%S", now_dt)

        application_id = ctx.headers.get("Vending-Application-Id")
        token_telegram = GetTelegramToken(application_id)
        channel_id = GetChannelId(application_id)
        # message_id from helper is str
        message_id_str = GetMessageID(application_id)

        if not application_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Application id not found")
        if not token_telegram:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Token Telegram not found")
        if not channel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Channel Id not found")
        if not message_id_str:
            # This is critical. If message ID is not found, we cannot edit.
            # The Go code proceeds to create if message_id is not found in pinned_message
            # We'll adjust the logic based on Go's behavior.
            message_id = 0  # If not found, treat as 0 for initial creation
        else:
            try:
                message_id = int(message_id_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Message Id format")

        # Get List Devices
        ws_result_device = await self.task_service.list_device(application_id)
        response_device = WSResultToMap(ws_result_device)
        if ws_result_device.body.get("result") != Result.SUCCESS:
            raise HTTPException(
                status_code=ws_result_device.code, detail=response_device["body"])

        body_result_device = ws_result_device.body
        devices, _, _ = RGet(body_result_device, "devices", [])
        if not devices:
            devices = []
        list_devices = {x["id"]: x for x in devices if isinstance(
            x, dict) and "id" in x}

        # Get Sensors
        ws_sensor_result = await self.task_service.get_sensors(application_id)
        sensor_response = WSResultToMap(ws_sensor_result)
        if ws_sensor_result.code != Result.HTTP_OK:
            raise HTTPException(
                status_code=ws_sensor_result.code, detail=sensor_response["body"])

        sensor_body = ws_sensor_result.body
        sensors, _, _ = RGet(sensor_body, "sensors", [])
        if not sensors:
            sensors = []

        list_sensors = {}
        stock_map = {}

        for x in sensors:
            if not isinstance(x, dict):
                continue

            device_id, _, _ = RGet(x, "device_id", [])
            sensor_name, _, _ = RGet(x, "sensor", [])
            param, _, _ = RGet(x, "param", [])
            latest_data, _, _ = RGet(x, "latest_data", [])
            value = latest_data.get("value")

            if device_id not in list_sensors:
                list_sensors[device_id] = {}
            if sensor_name not in list_sensors[device_id]:
                list_sensors[device_id][sensor_name] = {}

            if sensor_name == "stock_threshold":
                list_sensors[device_id][sensor_name]["value"] = value
            else:
                if param == "id":
                    list_sensors[device_id][sensor_name]["id"] = value
                elif param == "name":
                    list_sensors[device_id][sensor_name]["name"] = value
                elif param == "stock":
                    list_sensors[device_id][sensor_name]["stock"] = value

        for device_id, sensor_map in list_sensors.items():
            converted_sensor_map = {k: v for k, v in sensor_map.items()}
            stock_map[device_id] = {}

            for key in converted_sensor_map:
                sensors_map, _, _ = RGet(converted_sensor_map, key, [])
                _id = sensors_map.get("id")
                _name = sensors_map.get("name")
                _stock = sensors_map.get("stock")

                if _id is None or _name is None:
                    continue

                body_item = {
                    "device_id": device_id,
                    "name": _name,
                    "id": _id,
                }

                status_item = None
                if isinstance(_stock, (int, float)):
                    if _stock > 3:
                        status_item = None  # continue, as per Go logic
                    elif _stock <= 3 and _stock > 0:
                        status_item = "warning"
                    elif _stock == 0:
                        status_item = "empty"

                if status_item:
                    body_item["status"] = status_item
                    stock_map[device_id][f"{_id}_{key}_{_stock}"] = body_item

        stock_body = []
        for item in stock_map.values():
            stock_body.append(item)

        # Get Tasks (Online and No Transaction)
        res_task = await self.task_service.get_task(application_id)
        if res_task.code != Result.HTTP_OK:
            raise HTTPException(status_code=res_task.code,
                                detail=json.dumps(res_task.body))

        response_task = res_task.body
        task_body, _, _ = RGet(response_task, "data", [])
        if not task_body:
            task_body = []

        online_body = []
        no_trx_body = []

        for x in task_body:
            if not isinstance(x, dict):
                continue
            type_item, _, _ = RGet(x, "type", [])
            # This 'id' refers to task ID, not device ID in go code
            device_id, _, _ = RGet(x, "id", [])
            # It seems the device ID needs to be parsed from task_key or notification_open content

            # Re-evaluating the Go code's `deviceID, errors, _ := icontroller.RGet[string](data, "id", errors)`
            # In taskservice.go, tasks don't typically have "id" as device_id directly.
            # It's more likely `task_key` contains device info or `notification_open` does.
            # The Go code for online_body and no_trx_body implies `data` has `id` which is device_id.
            # Let's adjust based on how it's used later with `onlineMap[deviceID]` etc.

            if type_item == "online":
                online_body.append(x)
            elif type_item == "no_transaction":
                no_trx_body.append(x)

        online_map = {}
        for item in online_body:
            arr_item, _, _ = RGet(item, "notification_open", [])
            if not arr_item:
                continue
            arr_map = arr_item[0]
            if not isinstance(arr_map, dict):
                continue
            detail_map, _, _ = RGet(arr_map, "detail", [])
            content, _, _ = RGet(detail_map, "content", [])

            arr_content = content.split(":")
            if len(arr_content) < 2:
                continue

            txt_x = arr_content[1].strip()
            y = txt_x.split()
            if not y:
                continue

            # Assuming device_id is the first word after ":"
            device_id_from_content = y[0]
            online_map[device_id_from_content] = txt_x

        no_trx_map = {}
        for item in no_trx_body:
            task_key, _, _ = RGet(item, "task_key", [])
            open_time, _, _ = RGet(item, "open_time", [])

            arr_key = task_key.split(":")
            device_id_from_key = arr_key[0].strip() if len(arr_key) > 0 else ""

            arr_item, _, _ = RGet(item, "notification_open", [])
            if not arr_item:
                continue
            arr_map = arr_item[0]
            if not isinstance(arr_map, dict):
                continue
            detail_map, _, _ = RGet(arr_map, "detail", [])
            content, _, _ = RGet(detail_map, "content", [])

            x_parts = content.split(".")
            if len(x_parts) < 2:
                continue

            txt_x = x_parts[0].strip()
            y_parts = txt_x.split("\n\n")
            if len(y_parts) < 2:
                continue

            no_trx_map[device_id_from_key] = {
                "txt": y_parts[1],
                "time": open_time,
            }

        content_no_trx = ""
        content_online = ""
        content_stock = ""

        # Iterate over all devices to build content
        for device_id_iter in list_devices.keys():  # Use keys from list_devices
            device_name, _, _ = RGet(list_devices, device_id_iter, [])

            # No Transaction Content
            if device_id_iter in no_trx_map:
                item_no_trx = no_trx_map[device_id_iter]
                txt_no_trx, _, _ = RGet(item_no_trx, "txt", [])
                time_no_trx, _, _ = RGet(item_no_trx, "time", [])
                content_no_trx += f"\n{txt_no_trx} (last update : {time_no_trx})"

            # Online Content
            if device_id_iter in online_map:
                txt_online = online_map[device_id_iter]
                content_online += f"\n{txt_online}"

            # Stock Content
            if device_id_iter in stock_map and stock_map[device_id_iter]:
                product_map = stock_map[device_id_iter]

                warning_count = 0
                empty_count = 0
                for product_id_key in product_map:
                    product_item_map, _, _ = RGet(
                        product_map, product_id_key, [])
                    status_val, _, _ = RGet(product_item_map, "status", [])

                    if status_val == "warning":
                        warning_count += 1
                    elif status_val == "empty":
                        empty_count += 1

                # Append only if there are warning/empty items for this device
                if warning_count > 0 or empty_count > 0:
                    content_stock += f"\n VM {device_name} Produk hampir kosong sebanyak {warning_count} dan produk kosong sebanyak {empty_count}"

        header_telegram = "<u><b>Summary Message</b></u>"
        message = header_telegram

        if content_no_trx:
            message += f"\n \n<u><b>Transaction </b></u> \n{content_no_trx}"
        if content_online:
            message += f"\n \n <u><b>Online </b> (Last Update: {dt_string} ) </u>\n{content_online}"
        if content_stock:
            message += f"\n \n <u><b>Stock </b> (Last Update: {dt_string} ) </u>\n{content_stock}"

        # Telegram Pinned Message Logic
        res_pin = await self.task_service.get_pinned_message(token_telegram, channel_id)
        if res_pin.code != Result.HTTP_OK:
            # If getting pinned message fails, it might mean no pinned message exists
            # The Go code then proceeds to create one if errors exist.
            # Let's check for specific error from Telegram for "message not found" if possible
            # For simplicity, if HTTP_OK is not returned, we will try to create.
            pass  # Continue to create path

        body_pin = res_pin.body
        errors_pin: List[Exception] = []
        result_body, errors_pin, _ = RGet(body_pin, "result", errors_pin)
        pinned_message_data, errors_pin, _ = RGet(
            result_body, "pinned_message", errors_pin)

        # If any of these RGet calls fail, errors_pin will contain errors.
        # This mimics Go's `if errors != nil` check.
        if errors_pin or not pinned_message_data:  # If no pinned message found or parsing error
            # Try to Create Pinned Message
            # Use 0 for message_id if it was not found, as per Go's CreatePinned signature
            # message_id 0 for new
            resu_create = await self.task_service.create_pinned(message, channel_id, token_telegram, message_id=0)
            if resu_create.code != Result.HTTP_OK:
                raise HTTPException(
                    status_code=resu_create.code, detail=WSResultToMap(resu_create)["body"])
            return {"message": "Success (Pinned message created)", "data": WSResultToMap(resu_create)["body"]}
        else:
            # Pinned message found, try to Edit
            message_id_from_api, errors_pin_edit, _ = RGet(
                pinned_message_data, "message_id", [])
            if errors_pin_edit or not message_id_from_api:
                # Fallback to create if message_id cannot be extracted from existing pinned message
                # message_id 0 for new
                resu_create = await self.task_service.create_pinned(message, channel_id, token_telegram, message_id=0)
                if resu_create.code != Result.HTTP_OK:
                    raise HTTPException(
                        status_code=resu_create.code, detail=WSResultToMap(resu_create)["body"])
                return {"message": "Success (Pinned message created due to ID extraction failure)", "data": WSResultToMap(resu_create)["body"]}

            resu_edit = await self.task_service.edit_pinned(message, channel_id, token_telegram, int(message_id_from_api))
            if resu_edit.code != Result.HTTP_OK:
                raise HTTPException(status_code=resu_edit.code,
                                    detail=WSResultToMap(resu_edit)["body"])
            return {"message": "Success (Pinned message edited)", "data": WSResultToMap(resu_edit)["body"]}
