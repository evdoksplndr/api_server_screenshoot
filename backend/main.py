from typing import List, Tuple
import secrets
import csv
import io
import zipfile

from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Form
from fastapi import Response, Request, File, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse

from playwright.async_api import async_playwright

from data_base import Users, Session, update



app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def screen_page(request: Request, response: Response):
	token = request.cookies.get("token")
	print(token)
	session = Session()
	if token:
		print("TOKEN TRUE")
		user = session.query(Users).filter_by(generated_token=token).first()
		if user:
			print("USER TRUE")
			auth_user = (session.query(Users).
					filter(Users.passwd_hash == user.passwd_hash).
					first())
			if auth_user:
				print("UATR USER TRUE")
				return templates.TemplateResponse("screen_download.html",
					{
					"request": request,
					"response": "You authorized",
					"login_name": auth_user.login,
					"tryes": str(auth_user.limit),
					"tryes_spent": str(auth_user.limit_spent)
					}
					)
		session.close()

	if not token:
		print("no token \ creating")
		token = secrets.token_hex(32)
		print(token)
		session.add(Users(generated_token = token))
		session.commit()
		session.close()

	response = templates.TemplateResponse("screen_download.html",
				{
				"request": request,
				"response": "You authorized",
				"login_name": "",
				"tryes": "",
				"tryes_spent": "",
				}
				)

	response.set_cookie(

		key="token",
		value=token,
		httponly=True

		)


	return response

@app.get("/screenshot")
async def screen(request: Request,
		response: Response,
 		url: str,
		full_page: bool = False):

	session = Session()
	token = request.cookies.get("token")
	user_data = (
		session.query(Users).
		filter(Users.generated_token == token).
		first()
		)
	async with async_playwright() as p:
		browser = await p.chromium.launch(args=["--no-sandox"])
		page = await browser.new_page()

		if token:
			print(token)
			session.execute(
				update(Users)
				.where(Users.generated_token==token)
				.values(limit = Users.limit - 1)
			)
			session.execute(
				update(Users)
				.where(Users.generated_token==token)
				.values(limit_spent = Users.limit_spent + 1)
			)
		if not token:
			token = secrets.token_hex(32)
			user = Users(generated_token = token)
			response.set_cookie(key="token",
				 value=token,
				 httponly=True)
			session.add(user)
			session.commit()
			session.close()

		session.commit()
		session.close()
		await page.goto(url, wait_until="networkidle")

		img = await page.screenshot(full_page=full_page)

		await browser.close()

	return Response(img, media_type="image/png")

@app.get("/registration")
async def get_registr(request: Request):
	return templates.TemplateResponse("/registration.html", {
				"request": request
			})

@app.post("/registration")
async def post_registr(request: Request, response: Response,
			login: str = Form(),
			passwd: str = Form(),
			rep_passwd: str = Form()
			):
	print("POST ZAPROS PROSHEL")
	token = request.cookies.get("token")
	if token and passwd == rep_passwd:
		session = Session()
		print(token)
		session.execute(
			update(Users).
			where(Users.generated_token==token).
			values(login = login,
				passwd_hash = passwd)
				)
		auth_user = (
			session.
			query(Users).
			filter(Users.passwd_hash == passwd).first()
			)
		print("zbs proshlo")
		user_datka = [str(auth_user.limit),
				 str(auth_user.limit_spent)]
		session.commit()
		session.close()
		return templates.TemplateResponse("screen_download.html",
				{
				"request": request,
				"response": "You authorized",
				"login_name": login,
				"tryes": user_datka[0],
				"tryes_spent": user_datka[1]
				}
				)
	if not token:
		session = Session()
		token = secrets.token_hex(32)
		user = Users(generated_token = token
			)
		session.commit()
		session.close()
		print("no token| sozdan")
		return  FileResponse(path="templates/registration.html",
						 media_type="text/html")


@app.get("/login")
async def login(request: Request, response: Response):
	session = Session()
	token = request.cookies.get("token")

	if token:
		user = (
			session.
			query(Users).
			filter_by(generated_token=token).
			first()
		)
		if not user.passwd_hash:
			print("witout password")
			return templates.TemplateResponse(
				"login.html", {
				"request": request,
						}
				)

		if user.passwd_hash and user.login:
			return templates.TemplateResponse(
				"screen_download.html", {
				"request": request,
				"response": "You are authorized",
				"login_name": user.login,
				"tryes": str(user.limit),
				"tryes_spent": str(user.limit_spent)
						}
				)

		session.commit()
		session.close

	if not token:
		token = secrets.token_hex(32)
		response.set_cookie(
				key="token",
				value=token,
				httponly=True
			)
		user = Users(generated_token = token)
		session.add(user)
		session.commit()
		session.close


	return  template.TemplateResponse("login.html", {
		"request": request
			})


@app.post("/post_login")
async def post_login(request: Request,
			response: Response,
			login: str = Form(),
			passwd: str = Form()
				):
	session = Session()
	token = request.cookies.get("token")

	if token and passwd:
		print(f"token i pass True\n {token}")
		user_by_token = (session.query(Users).
			filter_by(generated_token=token).
			first())
		user_by_login = (session.
				query(Users).
				filter_by(login=login).
				first())
		if user_by_login.login == login and user_by_login.passwd_hash==passwd:
			response.set_cookie(
					key="token",
					value=user_by_login.generated_token,
					httponly=True)

			response = templates.TemplateResponse(
				"screen_download.html", {
				"request": request,
				"response": "You are authorized",
				"login_name": user_by_login.login,
				"tryes": str(user_by_login.limit),
				"tryes_spent": str(user_by_login.limit_spent)
						}
				)
			session.commit()
			session.close()
			return response

		else:
			return FileResponse(path="templates/login.html", media_type="text/html")

	else: pass

	if not token:
		token = secrets.token_hex(32)
		user = Users(generated_token = token)
		session.commit()
		session.close



@app.get("/aiyim")
async def aiyim():
	return FileResponse(path="templates/aiyim.html", media_type="text/html")


@app.get("/tg_pay")
async def tg_pat(request: Request, response: Response):
	token = request.cookies.get("token")
	url = f"https://t.me/apiscreen_bot?start={token}"
	return RedirectResponse(url)

@app.get("/info")
async def info(request: Request):
	return templates.TemplateResponse("info.html", {"request": request})


@app.post("/css_txt_screen")
async def many_scrrens(request: Request, response: Response,
			upload_file: UploadFile = File(...)):
	filename_list = []
	if upload_file.filename.endswith(".txt"):
		print(".txt file uploaded")
		async with async_playwright() as p:
			browser = await p.chromium.launch(args=["--no-sandbox"])
			page = await browser.new_page()
			content = await upload_file.read()
			text = content.decode("utf-8")
			urls_list = text.splitlines()
			for url in urls_list:
				await page.goto(url=url, wait_until="networkidle")
				print(url)
				img = await page.screenshot()
				name = (url.
					replace("https//:", "").
					replace("http//:", "").
					replace("/", "")
					)
				filename_list.append((name, img))
			zipbytes = await image_to_zip(images=filename_list)
			await page.close()
	if upload_file.filename.endswith(".csv"):
		async with async_playwright() as p:
			browser = await p.chromium.launch(args=["--no-sandbox"])
			page = await browser.new_page()
			read_file = await upload_file.read()
			content = read_file.decode("utf-8")
			reader = csv.reader(io.StringIO(content))
			for urls in reader:
				url = urls[0]
				await page.goto(url=url, wait_until="networkidle")
				print(url)
				img = await page.screenshot()
				name = (url.
					replace("https://", "").
					replace("http://", "").
					replace("/", '')
					)
				filename_list.append((name, img))
			zipbytes = await image_to_zip(images=filename_list)
			await page.close()
	return StreamingResponse(
		zipbytes,
		media_type="application/zip",
		headers = {
			"Content-Disposition": "attachment;"
			" filename=screenshots.zip"
			}
		)


async def image_to_zip(
		images: List[Tuple[str, bytes]],
	):
	zipbytes = io.BytesIO()
	with zipfile.ZipFile(zipbytes, "w", zipfile.ZIP_DEFLATED) as zip_file:
		for name, img in images:
			filename = f"{name}"
			print(f"{filename}, --- {img[:10]}")
			zip_file.writestr(filename, img)
		zip_file.close()
	zipbytes.seek(0)
	return zipbytes



