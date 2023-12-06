# 3 workers to refinery code
     # Distribute workers evenly among refineries
            refineries = self.structures(UnitTypeId.REFINERY).ready
            workers = self.workers.idle
 
            # Ensure that each refinery has exactly 3 workers
            desired_workers_per_refinery = 3
 
            for refinery in refineries:
                # Check if the refinery already has the desired number of workers
                if refinery.assigned_harvesters < desired_workers_per_refinery:
                    # Assign workers to the refinery up to the desired count
                    workers_to_assign = min(desired_workers_per_refinery - refinery.assigned_harvesters, len(workers))
                    for _ in range(workers_to_assign):
                        worker = workers.pop(0)  # Take the first worker from the list
                        worker.gather(refinery)