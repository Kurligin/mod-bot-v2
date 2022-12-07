# class random_file_name:
#
#     def generate_random_string(length):
#         import random
#         import string
#
#         letters = string.ascii_lowercase
#         rand_string = ''.join(random.choice(letters) for i in range(length))
#
#         return rand_string
#
#
# print(random_file_name.generate_random_string(16))
# # generate_random_string(16)

import random
import string

def generate_random_string(length):
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for i in range(length))
    
    return rand_string


print(generate_random_string(16))
# generate_random_string(16)
