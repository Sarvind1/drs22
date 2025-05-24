from prefect import flow, task
import random
import time

# Simulate data extraction from different sources
@task
def extract_data_source_a():
    time.sleep(1)
    return {"source": "A", "data": [random.randint(0, 100) for _ in range(5)]}

@task
def extract_data_source_b():
    time.sleep(1)
    return {"source": "B", "data": [random.randint(0, 100) for _ in range(5)]}

# Simulate data transformation
@task
def transform_data(data):
    time.sleep(1)
    transformed = [x * 2 for x in data["data"]]
    return {"source": data["source"], "data": transformed}

# Simulate data loading
@task
def load_data(data):
    time.sleep(1)
    print(f"Loaded data from source {data['source']}: {data['data']}")
    return True

# Simulate report generation
@task
def generate_report():
    time.sleep(1)
    print("Report generated.")
    return "report.pdf"

# Simulate sending notification
@task
def send_notification(report):
    time.sleep(1)
    print(f"Notification sent with report: {report}")
    return True

@flow
def complex_data_pipeline():
    # Extraction
    data_a = extract_data_source_a()
    data_b = extract_data_source_b()

    # Transformation
    transformed_a = transform_data(data_a)
    transformed_b = transform_data(data_b)

    # Loading
    load_result_a = load_data(transformed_a)
    load_result_b = load_data(transformed_b)

    # Reporting
    report = generate_report()

    # Notification
    send_notification(report)

if __name__ == "__main__":
    complex_data_pipeline()
