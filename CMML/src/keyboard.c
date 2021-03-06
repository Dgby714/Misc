#include "keyboard.h"
#include <string.h>

void keyboardPress(keyboardKey key)
{
	keyboardDown(key);
	keyboardUp(key);
}

uint32_t keyboardSend(const char *str)
{
	uint32_t len = (uint32_t)strlen(str), i = 0;
	for (i = 0; i < len; i++) keyboardPress(keyboardToKey(str[i]));
	return len;
}
