import re

# Safe math pattern: only numbers, operators, dots, and parentheses
MATH_PATTERN = re.compile(r"^[0-9\+\-\*\/\(\)\.\s]+$")

async def auto_calculator(client, message):
    text = message.text.strip()
    
    # Check if the message is a valid math equation and not too long
    if len(text) > 3 and len(text) < 50 and MATH_PATTERN.match(text):
        try:
            # Calculate the result safely
            result = eval(text)
            
            # Format result if it is a float
            if isinstance(result, float):
                result = round(result, 4)
            
            # Reply with the result
            await message.reply_text(
                f"<blockquote>🧮 <b>Result:</b> {result}</blockquote>", 
                parse_mode="html", 
                quote=True
            )
        except Exception:
            # Ignore invalid math expressions silently
            pass
