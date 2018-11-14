# HPMLA-CPU-OpenMPI Data Sharding
This recipe shows how to shred and deploy your training data prior to running a training job.  
This module is offered as is.  It was designed to fit one deployment.  We encourage you to change the code to match your own data scenario.

## Configuration
Please see refer to this [set of sample configuration files](./config) for
this recipe.

### Pool Configuration
The pool configuration should enable the following properties:
* The VM count should the VM count for the SymSGD training job minus one.  The SymSGD requires one VM to act as master node.
For an example: You plan to run your training job on 33 VMs.  You shred the data on 32 VMs.
* `inter_node_communication_enabled` must be set to `true`
* `max_tasks_per_node` must be set to 1 or omitted

### Global Configuration
The global configuration should set the following properties:
* `docker_images` array must have a reference to a valid HPMLA
Docker image that can be run with OpenMPI. The image denoted with `0.0.3`
tag found in [msmadl/symsgd_datasharding:0.0.3](https://hub.docker.com/r/msmadl/symsgd_datasharding/)
is compatible with Azure Batch Shipyard VMs.

### MPI Jobs Configuration (MultiNode)
The jobs configuration should set the following properties within the `tasks`
array which should have a task definition containing:
* `docker_image` should be the name of the Docker image for this container
invocation. For this example, this should be
`msmadl/symsgd_datasharding:0.0.3`.
Please note that the `docker_images` in the Global Configuration should match
this image name.
* `command` should contain the command to pass to the Docker run invocation.
For this HPMLA training example with the `msmadl/symsgd_datasharding:0.0.3` Docker image. The
application `command` to run would be:
`"/parasail/deploy_data.sh"`

* `multi_instance` property must be defined
  * `num_instances` should be set to `pool_current_dedicated`, or
    `pool_current_low_priority`

## Dockerfile and supplementary files
Supplementary files can be found [here](./docker).

You must agree to the following licenses prior to use:
* [High Performance ML Algorithms License](https://github.com/saeedmaleki/Distributed-Linear-Learner/blob/master/High%20Performance%20ML%20Algorithms%20-%20Standalone%20(free)%20Use%20Terms%20V2%20(06-06-18).txt)
* [TPN Ubuntu Container](https://github.com/saeedmaleki/Distributed-Linear-Learner/blob/master/TPN_Ubuntu%20Container_16-04-FINAL.txt)
* [Microsoft Third Party Notice](https://github.com/saeedmaleki/Distributed-Linear-Learner/blob/master/MicrosoftThirdPartyNotice.txt)
