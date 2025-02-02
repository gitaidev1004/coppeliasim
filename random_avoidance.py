import sim
import time
import random

# CopelliaSim 서버 연결 함수
def connect_to_sim():
    sim.simxFinish(-1)
    client_id = sim.simxStart('127.0.0.1', 19997, True, True, 5000, 5)
    if client_id == -1:
        print("Failed to connect to CopelliaSim.")
        return None
    print("Connected to CopelliaSim.")
    return client_id

# 센서 값 읽기 함수
def get_sensor_data(client_id, sensor_handles):
    distances = []
    for handle in sensor_handles:
        _, detection_state, detected_point, _, _ = sim.simxReadProximitySensor(client_id, handle, sim.simx_opmode_buffer)
        if detection_state:
            distances.append(detected_point[2])
        else:
            distances.append(float('inf'))
    return distances

# 랜덤 회피 로직
def random_avoidance(client_id, motor_handles, sensor_handles):
    left_motor, right_motor = motor_handles
    while True:
        distances = get_sensor_data(client_id, sensor_handles)
        min_distance = min(distances)

        if min_distance < 0.5:
            # 장애물이 감지되면 랜덤한 방향으로 회피
            direction = random.choice(['left', 'right'])
            if direction == 'left':
                sim.simxSetJointTargetVelocity(client_id, left_motor, 2.0, sim.simx_opmode_streaming)
                sim.simxSetJointTargetVelocity(client_id, right_motor, -2.0, sim.simx_opmode_streaming)
            else:
                sim.simxSetJointTargetVelocity(client_id, left_motor, -2.0, sim.simx_opmode_streaming)
                sim.simxSetJointTargetVelocity(client_id, right_motor, 2.0, sim.simx_opmode_streaming)
        else:
            sim.simxSetJointTargetVelocity(client_id, left_motor, 2.0, sim.simx_opmode_streaming)
            sim.simxSetJointTargetVelocity(client_id, right_motor, 2.0, sim.simx_opmode_streaming)

        time.sleep(0.1)

# 메인 함수
if __name__ == "__main__":
    client_id = connect_to_sim()
    if client_id:
        _, left_motor = sim.simxGetObjectHandle(client_id, 'left_motor', sim.simx_opmode_blocking)
        _, right_motor = sim.simxGetObjectHandle(client_id, 'right_motor', sim.simx_opmode_blocking)

        sensor_handles = []
        for i in range(1, 5):
            _, sensor_handle = sim.simxGetObjectHandle(client_id, f'sensor_{i}', sim.simx_opmode_blocking)
            sensor_handles.append(sensor_handle)

        for sensor in sensor_handles:
            sim.simxReadProximitySensor(client_id, sensor, sim.simx_opmode_streaming)

        try:
            random_avoidance(client_id, (left_motor, right_motor), sensor_handles)
        except KeyboardInterrupt:
            print("Stopping the simulation.")
            sim.simxFinish(client_id)