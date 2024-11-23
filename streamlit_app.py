import streamlit as st
import tempfile
import os
from multiprocessing import Process, Pipe
import time
import worker1, worker2  # Assuming these modules are in the same directory

# Function to start the worker processes
def start_workers(video_files, num_cameras):
    parent_conns = []
    processes = []

    workers = [worker1, worker2]  # You can add more workers as needed

    for i in range(num_cameras):
        parent_conn, child_conn = Pipe()
        parent_conns.append(parent_conn)

        # Dynamically assign video file and worker
        worker = workers[i % len(workers)]
        p = Process(target=worker.process_video, args=(video_files[i], child_conn))
        processes.append(p)
        p.start()

    return parent_conns, processes

# Function to retrieve vehicle counts from workers
def get_counts(parent_conns):
    counts = []
    for conn in parent_conns:
        if conn.poll():  # Check if there's data to read
            counts.append(conn.recv())
        else:
            counts.append(0)  # No data received means zero vehicles in the interval
    return counts

# Streamlit app main function
def main():
    st.title("Traffic Monitoring System")
    st.write("Upload videos for traffic analysis and monitor vehicle counts.")

    # Step 1: User selects the number of cameras
    num_cameras = st.selectbox("Select the number of cameras (1 to 4):", options=[1, 2, 3, 4])

    # Step 2: Video upload section
    st.write(f"Upload {num_cameras} video(s):")
    uploaded_files = []
    for i in range(num_cameras):
        file = st.file_uploader(f"Upload video for Camera {i + 1}:", type=["mp4"], key=f"camera_{i+1}")
        uploaded_files.append(file)

    # Check if all required videos are uploaded
    if st.button("Start Analysis"):
        if None in uploaded_files:
            st.error("Please upload all required videos.")
            return

        # Save uploaded files to temporary paths
        video_files = []
        for i, uploaded_file in enumerate(uploaded_files):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                tmp_file.write(uploaded_file.read())
                video_files.append(tmp_file.name)

        st.success("Videos uploaded successfully. Starting analysis...")

        # Step 3: Start worker processes
        parent_conns, processes = start_workers(video_files, num_cameras)

        try:
            # Step 4: Display real-time counts every 20 seconds
            st.write("Monitoring traffic. Vehicle counts will update every 20 seconds.")
            while True:
                time.sleep(20)
                counts = get_counts(parent_conns)
                max_count = max(counts)
                max_camera = counts.index(max_count) + 1

                st.write(f"Counts in last 20 seconds: {counts}")
                st.write(f"Camera with maximum vehicles moving towards: Camera {max_camera} with {max_count} vehicles")
        except KeyboardInterrupt:
            st.warning("Stopping traffic monitoring system...")
        finally:
            # Step 5: Cleanup processes and temporary files
            for p in processes:
                p.terminate()
            for conn in parent_conns:
                conn.close()
            for file in video_files:
                os.remove(file)

if __name__ == "__main__":
    main()
