"""
Example of using parallel execution framework for CyberCorp Node tests
"""

import asyncio
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.parallel_executor import ParallelExecutor, TaskBuilder, Task
from utils import CyberCorpClient, ClientManager, CommandForwarder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_parallel_commands():
    """Example: Execute multiple commands in parallel on a client"""
    
    # Setup
    client = CyberCorpClient(client_type="parallel_test", port=9998)
    await client.connect()
    
    manager = ClientManager(client)
    forwarder = CommandForwarder(client)
    
    # Find target client
    target_client = await manager.find_client_by_username("wjchk")
    if not target_client:
        logger.error("Target client not found")
        return
        
    client_id = target_client['id']
    
    # Build tasks using TaskBuilder
    builder = TaskBuilder()
    
    # Add parallel information gathering tasks
    info_tasks = builder.add_parallel([
        ("Get System Info", forwarder.forward_command, (client_id, "get_system_info")),
        ("Get Windows", forwarder.forward_command, (client_id, "get_windows")),
        ("Get Processes", forwarder.forward_command, (client_id, "get_processes")),
        ("Get Screen Size", forwarder.forward_command, (client_id, "get_screen_size"))
    ])
    
    # Add VSCode analysis (depends on windows info)
    vscode_task = builder.add(
        "Analyze VSCode",
        forwarder.forward_command,
        client_id, "vscode_get_content",
        dependencies=[info_tasks[1]],  # Depends on "Get Windows"
        timeout=10.0
    )
    
    # Add OCR task (independent)
    ocr_task = builder.add(
        "Screen OCR",
        forwarder.forward_command,
        client_id, "ocr_screen",
        kwargs={'params': {'x': 0, 'y': 0, 'width': 800, 'height': 600}},
        priority=1,  # Higher priority
        timeout=30.0
    )
    
    # Execute all tasks
    executor = ParallelExecutor(max_workers=4)
    executor.add_tasks(builder.build())
    
    # Show execution plan
    print("\nExecution Plan:")
    print(executor.visualize_dependencies())
    
    print("\nExecution Order (by levels):")
    for i, level in enumerate(executor.get_execution_order()):
        print(f"  Level {i+1}: {', '.join(level)}")
    
    # Execute
    print("\nExecuting tasks...")
    results = await executor.execute_all()
    
    # Show results
    print("\n" + "=" * 60)
    print("Execution Results")
    print("=" * 60)
    
    for task_id, result in results.items():
        print(f"\n{result.task_name}:")
        print(f"  Status: {result.status.value}")
        print(f"  Duration: {result.duration:.2f}s" if result.duration else "  Duration: N/A")
        
        if result.error:
            print(f"  Error: {result.error}")
        elif result.result:
            # Sample result
            result_str = str(result.result)
            if len(result_str) > 100:
                result_str = result_str[:100] + "..."
            print(f"  Result: {result_str}")
    
    # Cleanup
    await client.disconnect()


async def test_complex_workflow():
    """Example: Complex workflow with dependencies"""
    
    # Define workflow tasks
    async def check_server_status():
        """Check if server is running"""
        logger.info("Checking server status...")
        await asyncio.sleep(0.5)
        return {"status": "running", "port": 9998}
    
    async def find_clients(server_info):
        """Find available clients"""
        logger.info("Finding clients...")
        await asyncio.sleep(1.0)
        return ["client1", "client2", "wjchk"]
    
    async def analyze_client(client_name):
        """Analyze specific client"""
        logger.info(f"Analyzing {client_name}...")
        await asyncio.sleep(1.5)
        return {"client": client_name, "capabilities": ["ocr", "drag", "win32"]}
    
    async def run_ocr_test(client_info):
        """Run OCR test on client"""
        logger.info(f"Running OCR test on {client_info['client']}...")
        await asyncio.sleep(2.0)
        return {"client": client_info["client"], "ocr_result": "Test passed"}
    
    async def run_drag_test(client_info):
        """Run drag test on client"""
        logger.info(f"Running drag test on {client_info['client']}...")
        await asyncio.sleep(1.5)
        return {"client": client_info["client"], "drag_result": "Test passed"}
    
    async def generate_report(test_results):
        """Generate final report"""
        logger.info("Generating report...")
        await asyncio.sleep(0.5)
        return {"total_tests": len(test_results), "status": "All passed"}
    
    # Build complex workflow
    executor = ParallelExecutor(max_workers=3)
    
    # Level 1: Check server
    server_task = Task(
        id="server_check",
        name="Check Server",
        func=check_server_status
    )
    executor.add_task(server_task)
    
    # Level 2: Find clients (depends on server)
    clients_task = Task(
        id="find_clients",
        name="Find Clients",
        func=lambda: find_clients(executor.results["server_check"].result),
        dependencies=["server_check"]
    )
    executor.add_task(clients_task)
    
    # Level 3: Analyze each client (parallel)
    # In real scenario, we'd dynamically create these based on found clients
    for i, client in enumerate(["client1", "client2", "wjchk"]):
        analyze_task = Task(
            id=f"analyze_{client}",
            name=f"Analyze {client}",
            func=lambda c=client: analyze_client(c),
            dependencies=["find_clients"]
        )
        executor.add_task(analyze_task)
    
    # Level 4: Run tests on each client (parallel within each client)
    test_tasks = []
    for client in ["client1", "client2", "wjchk"]:
        # OCR test
        ocr_task = Task(
            id=f"ocr_{client}",
            name=f"OCR Test - {client}",
            func=lambda c=client: run_ocr_test({"client": c}),
            dependencies=[f"analyze_{client}"],
            priority=2
        )
        executor.add_task(ocr_task)
        test_tasks.append(ocr_task.id)
        
        # Drag test
        drag_task = Task(
            id=f"drag_{client}",
            name=f"Drag Test - {client}",
            func=lambda c=client: run_drag_test({"client": c}),
            dependencies=[f"analyze_{client}"],
            priority=1
        )
        executor.add_task(drag_task)
        test_tasks.append(drag_task.id)
    
    # Level 5: Generate report (depends on all tests)
    report_task = Task(
        id="report",
        name="Generate Report",
        func=lambda: generate_report([executor.results[t] for t in test_tasks]),
        dependencies=test_tasks
    )
    executor.add_task(report_task)
    
    # Show execution plan
    print("\nComplex Workflow Execution Plan:")
    print(executor.visualize_dependencies())
    
    # Execute workflow
    print("\nExecuting workflow...")
    results = await executor.execute_all()
    
    # Show summary
    successful = sum(1 for r in results.values() if r.status.value == "completed")
    print(f"\nWorkflow completed: {successful}/{len(results)} tasks successful")
    
    if "report" in results and results["report"].result:
        print(f"\nFinal Report: {results['report'].result}")


async def main():
    """Main example function"""
    print("CyberCorp Node Parallel Execution Examples")
    print("=" * 60)
    
    # Choose example
    print("\nSelect example:")
    print("1. Parallel client commands")
    print("2. Complex workflow with dependencies")
    
    choice = input("\nEnter choice (1-2): ").strip()
    
    if choice == "1":
        try:
            await test_parallel_commands()
        except Exception as e:
            logger.error(f"Example 1 failed: {e}")
            
    elif choice == "2":
        await test_complex_workflow()
        
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())