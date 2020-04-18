from random import choice

a_lower = ord('a')
a_upper = ord('A')

letters_lower = [chr(i) for i in range(a_lower, a_lower + 26)]
letters_upper = [chr(i) for i in range(a_upper, a_upper + 26)]
nums = [str(i) for i in range(0, 10)]


def generate_key(n):
    key = ''
    curr_syms = letters_lower + letters_upper + nums
    for i in range(n):
        key += choice(curr_syms)
    return key
