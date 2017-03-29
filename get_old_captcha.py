import string
fermer_head = 'Ты помогал фермеру, гоняясь за '
fermer_tail = '. У этой твари антитела'
food_head = 'Ты-то помнишь, '
food_tail = ', что точно безопасно,'

with open('history.txt', 'r') as input:
    with open('clear_captcha.txt', 'w') as output:
        text = input.read()
        lines = text.split('\n')
        for line in lines:
            if line.find('Ты помогал фермеру, гоняясь за ') != -1:

                head = line.find(fermer_head) + len(fermer_head)
                tail = line.find(fermer_tail)
                captcha = line[head:tail]
                output.write(captcha + '\n')

            if line.find(food_head) != -1:

                head = line.find(food_head) + len(food_head)
                tail = line.find(food_tail)
                captcha = line[head:tail]
                output.write(captcha + '\n')



