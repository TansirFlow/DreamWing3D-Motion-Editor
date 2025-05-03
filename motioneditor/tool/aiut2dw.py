with open('../motion/kick_ik/kick_ik_origin.txt') as file:
    lines = file.readlines()

origin_joint_list = ['time', 'head1', 'head2'] + [f"laj{i}" for i in range(1, 5)] + [f"llj{i}" for i in range(1, 7)] + [
    f"rlj{i}" for i in range(1, 7)] + [f"raj{i}" for i in range(1, 5)] + ['llj7', 'rlj7']
result_joint_list = ['time'] + [item for i in range(1, 7) for item in (f"llj{i}", f"rlj{i}")] + [item for i in
                                                                                                 range(1, 5) for item in
                                                                                                 (f"laj{i}",
                                                                                                  f"raj{i}")] + ['llj7',
                                                                                                                 'rlj7']
print(origin_joint_list)
print(result_joint_list)

output = ""
for line in lines:
    line = line.strip()
    data = line.split()
    data[0] = float(data[0]) / 1000
    phase = {}
    for i in range(len(data)):
        joint_name = origin_joint_list[i]
        angle = float(data[i])
        if joint_name in ['rlj2', 'rlj6', 'raj2', 'laj3', 'laj4']:
            angle = -angle
        phase[joint_name] = angle

    for i in range(len(result_joint_list)):
        joint_name = result_joint_list[i]
        output += str(phase[joint_name])
        if i != len(result_joint_list) - 1:
            output += " "
        else:
            output += "\n"
with open('output.txt', 'w') as file:
    file.write(output)