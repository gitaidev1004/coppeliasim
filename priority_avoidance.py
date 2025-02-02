import sim
import time

# CopelliaSim 서버 연결 함수
def connect_to_sim():
    sim.simxFinish(-1)  # 이전 연결 초기화
    client_id = sim.simxStart('127.0.0.1', 19997, True, True, 5000, 5)  # 서버 연결
    if client_id == -1:
        print("Failed to connect to CopelliaSim.")
        return None
    print("Connected to CopelliaSim.")
    return client_id

# 센서 값 읽기 함수
def get_sensor_data(client_id, sensor_handles):
    distances = []
    for handle in sensor_handles:
        # 센서 값 읽기
        _, detection_state, detected_point, _, _ = sim.simxReadProximitySensor(client_id, handle, sim.simx_opmode_buffer)
        if detection_state:  # 장애물 감지 시
            distances.append(detected_point[2])  # 감지된 거리 (z축 값)
        else:
            distances.append(float('inf'))  # 감지 실패 시 큰 값 반환
    return distances

# 센서 우선순위 기반 회피 로직
def priority_based_avoidance(client_id, motor_handles, sensor_handles):
    left_motor, right_motor = motor_handles
    while True:
        distances = get_sensor_data(client_id, sensor_handles)  # 센서 데이터 읽기

        # 센서 데이터 매핑 (예: 왼쪽 앞/오른쪽 앞)
        left_distance = distances[0]  # 좌측 센서
        right_distance = distances[1]  # 우측 센서

        print(f"Sensor readings: {distances}")

        if left_distance < 0.5:  # 왼쪽에 장애물
            print("Obstacle detected on the left! Turning right.")
            sim.simxSetJointTargetVelocity(client_id, left_motor, 2.0, sim.simx_opmode_streaming)  # 오른쪽 회전
            sim.simxSetJointTargetVelocity(client_id, right_motor, 0.5, sim.simx_opmode_streaming)
        elif right_distance < 0.5:  # 오른쪽에 장애물
            print("Obstacle detected on the right! Turning left.")
            sim.simxSetJointTargetVelocity(client_id, left_motor, 0.5, sim.simx_opmode_streaming)  # 왼쪽 회전
            sim.simxSetJointTargetVelocity(client_id, right_motor, 2.0, sim.simx_opmode_streaming)
        else:  # 장애물이 없으면 직진
            sim.simxSetJointTargetVelocity(client_id, left_motor, 2.0, sim.simx_opmode_streaming)
            sim.simxSetJointTargetVelocity(client_id, right_motor, 2.0, sim.simx_opmode_streaming)

        time.sleep(0.1)  # 0.1초 간격으로 반복

# 메인 함수
if __name__ == "__main__":
    # CopelliaSim 연결
    client_id = connect_to_sim()
    if client_id:
        # 자동차 모터 핸들 가져오기
        _, left_motor = sim.simxGetObjectHandle(client_id, 'left_motor', sim.simx_opmode_blocking)
        _, right_motor = sim.simxGetObjectHandle(client_id, 'right_motor', sim.simx_opmode_blocking)

        # 센서 핸들 가져오기
        sensor_handles = []
        for i in range(1, 5):  # sensor_1, sensor_2, sensor_3, sensor_4
            _, sensor_handle = sim.simxGetObjectHandle(client_id, f'sensor_{i}', sim.simx_opmode_blocking)
            sensor_handles.append(sensor_handle)

        # 센서 스트리밍 초기화
        for sensor in sensor_handles:
            sim.simxReadProximitySensor(client_id, sensor, sim.simx_opmode_streaming)

        # 장애물 회피 실행
        try:
            priority_based_avoidance(client_id, (left_motor, right_motor), sensor_handles)
        except KeyboardInterrupt:
            print("Stopping the simulation.")
            sim.simxFinish(client_id)  # 연결 종료
