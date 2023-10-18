from worker import worker

worker.control.purge()

print('Application started')

numTasks = 1
tasks = []

if __name__ == '__main__':
    for i in range(numTasks):
        tasks.append(
            worker.send_task('addTask', (i, 3))  # Send task by name
        )
        print('Sent task:', i)

    for task in tasks:
        result = task.get()
        print('Received result:', result)
    
    to = "manansoni.soni77@gmail.com"
    subject = "subject"
    msgHtml = "Hi<br/>Html Email"
    msgPlain = "Hi\nPlain Email"

    worker.send_task('sendGmail', (to, subject, msgHtml))
    
    worker.send_task('welcomeMail', ('mananrox77', to))

    print('Application ended')