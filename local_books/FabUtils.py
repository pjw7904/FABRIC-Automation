'''
Author: Peter Willis
Desc: Collection of scripts to aid in the testing of FABRIC experiments. 

THE SLICE MUST ALREADY BE CREATED FOR THIS TO WORK
'''

from fabrictestbed_extensions.fablib.fablib import FablibManager as fablib_manager

class FabOrchestrator:
    # Constructor, get access to the slice and nodes
    def __init__(self, sliceName):
        '''
        '''
        
        try:            
            # Slice
            self.slice = fablib_manager().get_slice(sliceName)

            # Nodes
            self.nodes = self.slice.get_nodes()

            print(f"Slice name: {sliceName}\nSlice and nodes were acquired successfully.")
 
        except Exception as e:
            print(f"Exception: {e}")

    def selectedNodes(self, prefixList=None):
        '''
        Perform an action (execute a command, up/download a file, etc.) on a subset of nodes
        '''
        
        if(prefixList):
            prefixList = tuple(map(str.strip, prefixList.split(",")))
        
        for node in self.nodes:
            nodeName = node.get_name()
            
            if(prefixList and not nodeName.startswith(prefixList)):
                continue
            
            yield node
            
    def executeCommandsParallel(self, command, prefixList=None):
        '''
        Execute a command, in parallel using threads, on all or a subset of remote FABRIC nodes
        '''
        
        print(f'Command executed: {command}')

        try:
            #Create execute threads
            execute_threads = {}
            for node in self.selectedNodes(prefixList):
                print(f"Starting command on node {node.get_name()}")
                execute_threads[node] = node.execute_thread(command)

            #Wait for results from threads
            for node,thread in execute_threads.items():
                print(f"Waiting for result from node {node.get_name()}")
                stdout,stderr = thread.result()
                print(f"stdout: {stdout}")
                print(f"stderr: {stderr}")

        except Exception as e:
            print(f"Exception: {e}")

        return

    def uploadDirectoryParallel(self, directory, remoteLocation=None, prefixList=None):
        '''
        '''
        
        if(remoteLocation is None):
            remoteLocation = "/home/rocky"
        
        print(f'Directory to upload: {directory}\nPlaced in: {remoteLocation}')

        try:
            #Create execute threads
            execute_threads = {}
            for node in self.selectedNodes(prefixList):
                print(f"Starting upload on node {node.get_name()}")
                execute_threads[node] = node.upload_directory_thread(directory, remoteLocation)

            #Wait for results from threads
            for node,thread in execute_threads.items():
                print(f"Waiting for result from node {node.get_name()}")
                output = thread.result()
                print(f"Output: {output}")

        except Exception as e:
            print(f"Exception: {e}")

        return    

    def saveSSHCommands(self):
        '''
        Grab the SSH command for each node in the topology and save it to a file in the local directory
        '''
        
        with open(f"{self.slice.get_name()}_ssh_cmds.txt", "w") as sshFile:
            for node in self.nodes:
                sshFile.write(f"{node.get_name()}:\n")
                sshFile.write(f"{node.get_ssh_command()}\n")

        return