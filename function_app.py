from urllib.parse import urlparse
import azure.functions as func
import logging

from core.bot import bot, dp, SECRET_TOKEN


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route("tg_webhook", methods=["POST"])
async def tg_webhook(req: func.HttpRequest) -> func.HttpResponse:
    if SECRET_TOKEN is not None:
        if req.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET_TOKEN:
            return func.HttpResponse("Invalid secret token", status_code=403)
    try:
        req_body = req.get_json()
    except ValueError as exc:
        logging.error(exc)
        return func.HttpResponse("Invalid request body", status_code=400)
    else:
        logging.debug(f"Processing: {req_body}")
        resp = await dp.feed_webhook_update(bot, req_body)
        if resp is not None:
            logging.warning("Response is not None: %r", resp)
        return func.HttpResponse(status_code=200)


@app.route(f"set_webhook/{SECRET_TOKEN}")
async def set_webhook(req: func.HttpRequest) -> func.HttpResponse:
    parsed_url = urlparse(req.url)
    scheme = parsed_url.scheme
    netloc = parsed_url.netloc

    webhook_url = f"{scheme}://{netloc}/api/tg_webhook"

    try:
        logging.info("Deleting webhook")
        await bot.delete_webhook()
        logging.info(f"Setting webhook to {webhook_url}")
        await bot.set_webhook(webhook_url, secret_token=SECRET_TOKEN)
        return func.HttpResponse(f"Webhook set to {webhook_url}", status_code=200)
    except Exception as exc:
        logging.error(f"Error setting webhook: {exc}")
        return func.HttpResponse("Failed to set webhook", status_code=500)
