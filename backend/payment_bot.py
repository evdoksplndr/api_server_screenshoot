import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from data_base import Users, Session, update

class User_data(StatesGroup):
	user_verification_state = State()
	wants_limit_state = State()
	paying_state = State()


TOKEN = "7734455182:AAGhmZdOq0b66tX-O1FX9rEyJaTo8cQVOv0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject,
				state: FSMContext):
	token = command.args
	if token:
		print(token)
		session = Session()
		user = session.query(Users).filter_by(generated_token=token).first()
		if user.login:
			print("login exists")
			await state.update_data(
				user_login = user.login,
				user_id = user.id,
				user_token = user.generated_token,
				limits_now = user.limit,
					)
			await message.answer(
				f"Hello {user.login}!\n"
        			f"write me how much limit are you want buy"
    				)
			await state.set_state(User_data.wants_limit_state)



		else:
			await message.answer("You have not an account,"
				"create please to continue\n"
				"URL - http://api-screen.site/registration"
				)
	if not token:
		print("no token")
		await message.answer(
			"Please, go to site and sign in to pay\n"
			"URL - http://api-screen.site/"
			)


@dp.message(User_data.wants_limit_state)
async def how_many_limits(message: Message, state: FSMContext):
	want_limits = message.text
	session = Session()
	data = await state.get_data()
	try:
		want_limits = int(want_limits)
	except:
		await message.answer("Enter number please")

	if isinstance(want_limits, int):
		await message.answer(f"OK{data.get('user_login')} you want to buy {want_limits}?\n"
					"NA URL SUKA!!!!!!!!!!!!!")

async def main():
	print("Бот запущен...")
	await dp.start_polling(bot)

def add_limit(paid: str, user_id: int, limits_add: int):
	session = Session()
	user = session.query(Users).filter_by(user_id).first()
	if paid:
		user.limit += limits_add
		session.commit()


if __name__ == "__main__":
    asyncio.run(main())
