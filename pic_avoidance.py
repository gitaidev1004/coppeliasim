import sim
import time

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

# PID 기반 회피 로직
def pid_controller_avoidance(client_id, motor_handles, sensor_handles, kp=1.0, ki=0.0, kd=0.5):
    left_motor, right_motor = motor_handles
    prev_error = 0
    integral = 0

    while True:
        distances = get_sensor_data(client_id, sensor_handles)
        left_distance = distances[0]
        right_distance = distances[1]

        error = 0.5 - left_distance  # 왼쪽 센서 기준 에러 계산
        integral += error
        derivative = error - prev_error

        # PID 제어
        left_speed = 2.0 + kp * error + ki * integral + kd * derivative
        right_speed = 2.0 - kp * error - ki * integral - kd * derivative

        # 속도 제한
        left_speed = max(-2.0, min(2.0, left_speed))
        right_speed = max(-2.0, min(2.0, right_speed))

        sim.simxSetJointTargetVelocity(client_id, left_motor, left_speed, sim.simx_opmode_streaming)
        sim.simxSetJointTargetVelocity(client_id, right_motor, right_speed, sim.simx_opmode_streaming)

        prev_error = error
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
            pid_controller_avoidance(client_id, (left_motor, right_motor), sensor_handles)
        except KeyboardInterrupt:
            print("Stopping the simulation.")
            sim.simxFinish(client_id)

