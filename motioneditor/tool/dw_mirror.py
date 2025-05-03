robot_type=0
ignore_arm=True
input_file="../motion/Kick_15M_t4.txt"

with open(input_file) as file:
    lines = file.readlines()

output = ''

for line in lines:
    line = line.strip()
    data = line.split()
    line_list=[data[0],data[2],data[1],data[4],data[3],data[6],data[5],data[8],data[7],data[10],data[9],data[12],data[11],data[14],data[13],data[16],data[15],data[18],data[17],data[20],data[19],data[22],data[21]]
    for i in range(len(line_list)):
        value=line_list[i]
        if i!=len(line_list)-1:
            output+=f"{value} "
        else:
            output+=f"{value}\n"

with open('output_mirror.txt', 'w') as file:
    file.write(output)