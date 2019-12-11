from src.components.optimizer import NetworkOptimizer



if __name__ == '__main__':
    # Initialize a Network Optimizer
    n_opt = NetworkOptimizer()

    # Load the topology from the server
    n_opt.load_topology()

    # Create flows using dijkstra
    n_opt.simple_optimization()

    print "Once tests are over press enter to delete flows...\n"
    raw_input()

    # Delete all the flows created during optimization
    n_opt.flow_manager.delete_all_flows()