from mtcollector import MultiThreadConnector

def MTCollector(devices, 
                shows, 
                loglevel: str = 'error', 
                max_threads: int = 12, 
                user: str = '', 
                paswd: str = '', 
                os_type: str = 'cisco_xr', 
                log_filename: str = None
                ) -> MultiThreadConnector:

    output_collected = MultiThreadConnector.output_collector(devices, 
                                                            shows, 
                                                            loglevel, 
                                                            max_threads, 
                                                            user,
                                                            paswd,
                                                            os_type,
                                                            log_filename)
    
    return output_collected
                                                        