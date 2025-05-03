robot_type=0
ignore_arm=False
input_file="../motion/Apollo_Open_Motion/Kick_15M_t0_Right.txt"

with open(input_file) as file:
    lines = file.readlines()

output = '<?xml version="1.0" encoding="utf-8"?>\n<behavior description="Kick motion with right leg" auto_head="1">\n\n'

for line in lines:
    line = line.strip()
    data = line.split()
    data[0] = float(data[0])
    output+=f'\t<slot delta="{data[0]}">\n'
    for i in range(1,len(data)):
        joint_id=i+1
        if ignore_arm and joint_id in [14,15,16,17,18,19,20,21]:
            continue
        if robot_type!=4 and (joint_id==22 or joint_id==23):
            continue
        angle = float(data[i])
        output+=f'\t\t<move id="{joint_id}" angle="{angle}"/>\n'
    output+='\t</slot>\n'
output+='</behavior>'

with open('output_fcp.xml', 'w') as file:
    file.write(output)