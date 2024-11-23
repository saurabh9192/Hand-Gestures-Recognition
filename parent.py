from multiprocessing import Process, Pipe
import time

# Import worker modules (each of these should have `process_video` function defined as above)
import worker1, worker2

def get_counts(parent_conns):
    counts = []
    for conn in parent_conns:
        if conn.poll():  # Check if there's data to read
            counts.append(conn.recv())
        else:
            counts.append(0)  # No data received means zero vehicles in the interval
    return counts

def main():
    # Create pipes and processes for each worker
    parent_conns = []
    processes = []
    for i, worker in enumerate([worker1, worker2]):
        parent_conn, child_conn = Pipe()
        parent_conns.append(parent_conn)
        p = Process(target=worker.process_video, args=(f'Video_Highway{i+1}.mp4', child_conn))
        processes.append(p)
        p.start()
    
    try:
        while True:
            time.sleep(20)  # Wait for 20 seconds
            counts = get_counts(parent_conns)
            max_count = max(counts)
            max_camera = counts.index(max_count) + 1
            
            print(f"Counts in last 20 seconds: {counts}")
            print(f"Camera with maximum vehicles moving towards: Camera {max_camera} with {max_count} vehicles")
    
    except KeyboardInterrupt:
        print("Stopping traffic management system...")
    finally:
        for p in processes:
            p.terminate()
        for conn in parent_conns:
            conn.close()

if __name__ == "__main__":
    main()
