from src.components.optimizer import NetworkOptimizer



if __name__ == '__main__':
    # Initialize a Network Optimizer
    n_opt = NetworkOptimizer()

    # Load the topology from the server
    n_opt.load_topology()

    # Run the Load Balancer deamon. By sending a SIGSTP (CTR Z) signal from terminal
    # the script will catch it and raise a SystemExit exception, terminating the script 
    # and returning the network in it's initila state
    try :
        n_opt.load_balancer_demon()
    except SystemExit:
        print '\nExiting...'

    # Delete all the flows created during optimization
    n_opt.flow_manager.delete_all_flows()