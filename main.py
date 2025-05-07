import os
import json
import random
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.types import FSInputFile 


BOT_TOKEN = "7865160360:AAFQTzTEGRkYdhEMf3TekrXcjH-24zbC_sw"
IMAGES_FOLDER = "images"
QUESTIONS_FILE = "questions.json"


bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


class QuizState(StatesGroup):
    playing = State()

def load_questions():
    
    if not os.path.exists(QUESTIONS_FILE):
        return []
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_keyboard(correct, wrongs):
    
    builder = ReplyKeyboardBuilder()
    options = wrongs + [correct]
    random.shuffle(options)
    for option in options:
        builder.add(types.KeyboardButton(text=option))
    builder.adjust(2)
    builder.row(types.KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)

@router.message(Command("start"))
async def start(message: types.Message):
    
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🎮 Играть"))
    await message.answer(
        "🎲 Добро пожаловать в викторину!\nНажмите 'Играть' чтобы начать!",
        reply_markup=builder.as_markup()
    )

@router.message(lambda message: message.text == "🎮 Играть")
async def start_game(message: types.Message, state: FSMContext):
    
    questions = load_questions()
    if not questions:
        await message.answer("❌ В базе нет вопросов! Добавьте вопросы в questions.json")
        return
    
    random.shuffle(questions)
    await state.set_state(QuizState.playing)
    await state.update_data(
        questions=questions,
        index=0,
        score=0
    )
    await ask_question(message, state)

async def ask_question(message: types.Message, state: FSMContext):
    
    data = await state.get_data()
    questions = data["questions"]
    index = data["index"]
    
    if index >= len(questions):
        random.shuffle(questions)
        await state.update_data(questions=questions, index=0)
        index = 0
    
    question = questions[index]
    image_path = os.path.join(IMAGES_FOLDER, question["image"])
    
    try:
        
        photo = FSInputFile(image_path)
        await message.answer_photo(
            photo,
            caption=f"❓ Вопрос {data['score'] + 1}/20",
            reply_markup=generate_keyboard(
                question["correct_answer"],
                question["wrong_answers"]
            )
        )
    except FileNotFoundError:
        await message.answer(f"❌ Файл изображения {question['image']} не найден!")
        return await start(message)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")
        return await start(message)
    
    await state.update_data(index=index + 1)

@router.message(QuizState.playing)
async def check_answer(message: types.Message, state: FSMContext):
   
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Игра остановлена", reply_markup=types.ReplyKeyboardRemove())
        return await start(message)
    
    data = await state.get_data()
    questions = data["questions"]
    question = questions[data["index"] - 1]
    
    if message.text == question["correct_answer"]:
        new_score = data["score"] + 1
        await state.update_data(score=new_score)
        
        if new_score >= 20:
            await state.clear()
            await message.answer(
                "🎉 Поздравляем! Вы ответили на 20 вопросов правильно!",
                reply_markup=types.ReplyKeyboardRemove()
            )
            return await start(message)
        
        await message.answer("✅ Правильно! Следующий вопрос:")
        return await ask_question(message, state)
    
    await state.clear()
    await message.answer(
        f"❌ Неверно! Правильный ответ: {question['correct_answer']}\n"
        f"Ваш результат: {data['score']} правильных ответов",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await start(message)

async def main():
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())