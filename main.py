from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import math

import os
TOKEN = os.getenv("TOKEN")

ANCHO, ALTO, OTRA, VER_CORTES = range(4)

# PRECIOS
precios = {
    "chambrana": 621,
    "riel": 350,
    "zoclo": 621,
    "cabezal": 350,
    "cerco": 350,
    "traslape": 350
}

# --- FUNCIONES ---

def calcular_aluminio_detallado(ventanas):
    totales = {
        "chambrana": 0,
        "riel": 0,
        "zoclo": 0,
        "cabezal": 0,
        "cerco": 0,
        "traslape": 0
    }

    def sumar(tipo, medida_cm, cantidad):
        totales[tipo] += (medida_cm / 100) * cantidad

    for ancho, alto in ventanas:
        medida = (ancho - 16) / 2

        sumar("chambrana", ancho, 1)
        sumar("riel", ancho, 1)
        sumar("zoclo", medida, 2)
        sumar("cabezal", medida, 2)
        sumar("chambrana", alto - 2.8, 2)
        sumar("cerco", alto - 3, 1)
        sumar("traslape", alto - 3, 1)
        sumar("cerco", alto - 3.5, 1)
        sumar("traslape", alto - 3.5, 1)

    total = 0
    detalle = "🧱 ALUMINIO:\n\n"

    for tipo, metros in totales.items():
        if metros > 0:
            tramos = math.ceil(metros / 3)
            metros_compra = tramos * 3

            costo_por_metro = precios[tipo] / 6
            costo = metros_compra * costo_por_metro

            total += costo

            detalle += (
                f"{tipo.capitalize()}: {round(metros,2)} m → "
                f"compras {metros_compra} m = ${round(costo,2)}\n"
            )

    detalle += f"\nSubtotal aluminio: ${round(total,2)}"

    return total, detalle


def calcular_vidrio(ventanas):
    medios = 0
    completos = 0

    for ancho, alto in ventanas:
        if alto <= 120:
            medios += math.ceil(ancho / 180)
        elif alto <= 240:
            completos += math.ceil(ancho / 180)

    completos += medios // 2
    medios = medios % 2

    costo = (completos * 1300) + (medios * 650)

    detalle = f"🪟 CRISTAL:\n{completos} hojas completas + {medios} medios\nCosto: ${costo}"

    return costo, detalle


def generar_cortes(ancho, alto):
    cortes = []

    medida = (ancho - 16) / 2

    cortes.append(f"🔹 Chambrana: 1 pza de {ancho} cm")
    cortes.append(f"🔹 Riel: 1 pza de {ancho} cm")
    cortes.append(f"🔹 Zoclo: 2 pzas de {medida} cm")
    cortes.append(f"🔹 Cabezal: 2 pzas de {medida} cm")

    cortes.append(f"🔹 Chambrana: 2 pzas de {alto - 2.8} cm")
    cortes.append(f"🔹 Cerco: 1 pza de {alto - 3} cm")
    cortes.append(f"🔹 Traslape: 1 pza de {alto - 3} cm")
    cortes.append(f"🔹 Cerco: 1 pza de {alto - 3.5} cm")
    cortes.append(f"🔹 Traslape: 1 pza de {alto - 3.5} cm")

    return "\n".join(cortes)


# --- CONVERSACIÓN ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ventanas"] = []
    await update.message.reply_text("📏 Dime el ANCHO en cm:")
    return ANCHO


async def recibir_ancho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["ancho"] = float(update.message.text)
        await update.message.reply_text("📐 Dime el ALTO en cm:")
        return ALTO
    except:
        await update.message.reply_text("❌ Número inválido")
        return ANCHO


async def recibir_alto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        alto = float(update.message.text)
        ancho = context.user_data["ancho"]

        context.user_data["ventanas"].append((ancho, alto))

        teclado = [["Sí", "No"]]
        await update.message.reply_text(
            "¿Quieres agregar otra ventana?",
            reply_markup=ReplyKeyboardMarkup(teclado, one_time_keyboard=True)
        )
        return OTRA

    except:
        await update.message.reply_text("❌ Número inválido")
        return ALTO


async def otra_ventana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    respuesta = update.message.text

    if respuesta == "Sí":
        await update.message.reply_text("📏 Dime el ANCHO:")
        return ANCHO

    else:
        ventanas = context.user_data["ventanas"]

        total_aluminio, detalle_aluminio = calcular_aluminio_detallado(ventanas)
        costo_vidrio, detalle_vidrio = calcular_vidrio(ventanas)

        total_final = total_aluminio + costo_vidrio

        teclado = [["Sí", "No"]]

        await update.message.reply_text(
            f"{detalle_aluminio}\n\n"
            f"{detalle_vidrio}\n\n"
            f"💵 TOTAL: ${round(total_final,2)}\n\n"
            f"¿Quieres ver los cortes?",
            reply_markup=ReplyKeyboardMarkup(teclado, one_time_keyboard=True)
        )

        return VER_CORTES


async def mostrar_cortes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Sí":
        ventanas = context.user_data["ventanas"]

        mensaje = "🧾 CORTES:\n\n"

        for i, (ancho, alto) in enumerate(ventanas, start=1):
            mensaje += f"🪟 Ventana {i} ({ancho}x{alto}):\n"
            mensaje += generar_cortes(ancho, alto)
            mensaje += "\n\n"

        await update.message.reply_text(mensaje)

    else:
        await update.message.reply_text("👍 Listo")

    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelado")
    return ConversationHandler.END


# --- BOT ---

app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ANCHO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ancho)],
        ALTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_alto)],
        OTRA: [MessageHandler(filters.TEXT & ~filters.COMMAND, otra_ventana)],
        VER_CORTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, mostrar_cortes)],
    },
    fallbacks=[CommandHandler("cancel", cancelar)],
)

app.add_handler(conv)

app.run_polling()
