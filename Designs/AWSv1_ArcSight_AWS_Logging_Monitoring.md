\[customer\]

ArcSight AWS Logging and Monitoring.

**Author**

**Roshan Ratnayake**

# Table of Contents {#table-of-contents .TOC-Heading}

[Overview [3](#overview)](#overview)

[Design Proposal [3](#_Toc49928307)](#_Toc49928307)

[Sizing figures (rule of thumb)
[5](#sizing-figures-rule-of-thumb)](#sizing-figures-rule-of-thumb)

[Capacity Design - Traffic & Bandwidth
[6](#capacity-design---traffic-bandwidth)](#capacity-design---traffic-bandwidth)

[Logger/ESM AWS Configuration
[6](#loggeresm-aws-configuration)](#loggeresm-aws-configuration)

[VPCs [7](#vpcs)](#vpcs)

[Security Groups [7](#security-groups)](#security-groups)

[Route 53 [8](#route-53)](#route-53)

[EC2 -- Key Pair [9](#ec2-key-pair)](#ec2-key-pair)

[EC2 [10](#ec2)](#ec2)

[Linux [15](#linux)](#linux)

[Disk IO [15](#disk-io)](#disk-io)

[Extra Packages [16](#extra-packages)](#extra-packages)

[Filesystem Configurations
[16](#filesystem-configurations)](#filesystem-configurations)

[Partitions [16](#partitions)](#partitions)

[Hostname [18](#hostname)](#hostname)

[ArcSight ESM [18](#arcsight-esm)](#arcsight-esm)

[Distributed Node -- mbus_data
[19](#distributed-node-mbus_data)](#distributed-node-mbus_data)

[Hyper threading [20](#hyper-threading)](#hyper-threading)

[ArcSight ESM [21](#arcsight-esm-1)](#arcsight-esm-1)

[Packer Optimization [21](#packer-optimization)](#packer-optimization)

[Ingestion Buffers [21](#ingestion-buffers)](#ingestion-buffers)

[Manager Java Heap Size
[21](#manager-java-heap-size)](#manager-java-heap-size)

[Performance [22](#performance)](#performance)

[CPU [22](#cpu)](#cpu)

[Memory [23](#memory)](#memory)

[Swap [23](#swap)](#swap)

[Disk [24](#disk)](#disk)

[Disk IO/s (IOPs) [24](#disk-ios-iops)](#disk-ios-iops)

[Disk Throughput [25](#disk-throughput)](#disk-throughput)

[Disk Utilization [25](#disk-utilization)](#disk-utilization)

[Disk IO Time (Latency)
[26](#disk-io-time-latency)](#disk-io-time-latency)

[Disk Queue Depth (Avg)
[27](#disk-queue-depth-avg)](#disk-queue-depth-avg)

[Network [27](#network)](#network)

[Final Remarks [29](#final-remarks)](#final-remarks)

[Reference material [29](#reference-material)](#reference-material)

#  {#section .•Table-Heading}

#  {#section-1 .•Table-Heading}

# Overview {#overview .•Table-Heading}

\[customer\] CDRC provide a SOC function utilizing existing and mature
ArcSight Secure Data Platform for Threat Detection. \[customer\] are
migrating applications onto AWS and require Threat Detection utilizing
the same centralize SOC function with minimal footprint in the AWS
tenant.

\[customer\] already have ArcSight ESM, Logger and SmartConnectors
deployed to monitor on-premise networking.

\[customer\] have a (1GB) AWS Direct Connect.

This document is to provide a High Level options and guidance on Threat
Detection of the AWS tenancy utilizing existing ArcSight platform and
SOC Capability.

\[customer\] has multiple CloudWatch (5) configured and looking to
consolidated into single CloudWatch.

\[Customer\] is moving workloads from their on-premises data center into
AWS as part of its Digital Transformation strategy. \[Customer\] intends
to enable its Security Operations to seamlessly monitor workloads moving
to AWS. \[Customer\] has an internal SOC capability and a mature
ArcSight SIEM, with an integrated after-hours handoff to NTT via the
forwarding of logs to the NTT ArcSight SOC environment. \[Customer\]
will also engage Amazon Managed Security Services to monitor AWS
workloads. It is expected that the transition of workloads to AWS will
utilize the existing capacity licensing already provided via ArcSight
SIEM. The following details the monitoring design for \[Customer\]\'s
SOC environment and AWS. AWS will utilize its existing Splunk capability
to monitor the \[Customer\] environment. Both teams will need access to
the same level of data for incident response.

# AMS Logging Design {#ams-logging-design .•Table-Heading}

<!-- IMAGE: image-001 | {{caption}} -->{width="6.768055555555556in"
height="3.8993055555555554in"}

[]{#_Toc49928307 .anchor}Description of solution:

1\. Logs to be stored in CloudWatch. The CloudWatch Agent works on the
endpoint and ships logs to the CloudWatch console in the account.

2\. Generation:

• At the time of account onboarding, AMS configures baseline monitoring
(a

combination of CW alarms, and CW event rules) for all your resources
created in a managed account. The baseline monitoring configuration
generates an alert when a CloudWatch (CW) alarm is triggered or a CW
event is generated. Even if AWS services such as Managed Active
Directory (AD) do not generate CW events by default, AMS transforms them
into a CW event for easier processing. In addition to using CloudWatch,
AMS also processes notifications from services such as Managed AD
directly.

• AMS through their SOC provides monitoring of events based on GuardDuty
as their primary detection control. If alerts are raised, AMS operations
will take proactive actions to protect your account and resources.

• As for GuardDuty: GuardDuty analyzes continuous streams of meta-data
generated from your account and network activity found in AWS CloudTrail
Events, Amazon VPC Flow Logs, and DNS Logs. It also uses integrated
threat intelligence such as known malicious IP addresses, anomaly
detection, and machine learning to identify threats more accurately.
GuardDuty is a monitored AMS service.

GuardDuty finding\
types: https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_findi
ng-types-active.html

• There are Finding Types where it makes sense for VHA to lead the
response, e.g. UnauthorizedAccess:IAMUser/ConsoleLogin. Because user
lifecycle management is VHA responsibility, AMS ensures delivery of the
alert to your team for review, but will not take further action unless
you let us know the behavior is illegitimate.

3\. Aggregation:

-   All alerts generated by your resources are sent to the AMS
    monitoring

> system by directing them to an SNS topic in the account. The AMS
> monitoring system is known as MMS; system components named with
> \"mms\" refer to resources in AWS accounts that the AMS monitoring
> system relies on.

-   GuardDuty findings will be forwarded to CloudWatch and from there to
    an SNS topic (what is\
    SNS?: https://docs.aws.amazon.com/sns/latest/dg/welcome.html)

-   GuardDuty findings will be also available in AWS Security Hub for
    the VHA CDRC team to review and address using that interface

4\. Processing in AMS:\
• AMS analyzes the alerts and processes them based on their potential
for

impact. Alerts are processed as described next.

1.  Alerts with known customer impact: These lead to the creation of a

> new incident report and AMS follows the incident management process;
> for details on incident management, see Incident Management. Example
> alert: An EC2 instance fails a system health check, AMS attempts to
> recover the instance by stopping and restarting it.

2.  Alerts with uncertain customer impact: For these types of alerts,
    AMS sends a service notification that posts to your Service Requests
    page, asking you to verify the impact before we classify the alert
    as an incident. For example: An alert for \>85% CPU utilization for
    more than 10 minutes on an EC2 instance cannot be immediately
    categorized as an incident since this behavior may be expected based
    on usage. For such alerts, AMS sends an alert notification with the
    details and checks if the alert needs mitigating action. Alert
    notifications are discussed in detail in this section. We offer
    options for mitigating actions in the notification, and your reply
    that

confirms that the alert is an incident triggers the creation of a new
incident report and the AMS incident management process. Any service
notification that receives a response of \"no customer impact\", or no
response at all, is marked as resolved and the corresponding alert is
marked as resolved.

3\. Alerts with no customer impact: If, after evaluation, AMS determines
that the alert does not have customer impact, the alert is closed. For
example: Amazon GuardDuty finds unusual network port activity but upon
investigation it is found to be a result of the patching process.

5\. Processing by the VHA CDRC team:

-   CDRC will receive automated notifications through Email and/or SMS

-   Will provide us with:

    1.  email addresses (e.g. group mailboxes) or phone numbers -- those
        would used to subscribe those to the SNS topic.

    2.  decide which GuardDuty alert types they would like to be
        notified about (those can be all or only a subset)

    3.  Should email or SMS not be enough and you would like to pursue
        integration with ArcSIght, SNS supports also Lambda (AWS
        Service), SQS (AWS Service), HTTP/S (requirements listed\
        here: https://docs.aws.amazon.com/sns/latest/dg/sns-http-https-
        endpoint-as-subscriber.html) to send event data across.

-   GuardDuty findings will be also available in AWS Security Hub for
    the VHA CDRC team to review and address using that interface

> About this solution

1.  Level of effort is low. Most functionality is 'out-of-the-box' and
    allows to

> ensure relevant logging and monitoring is in place in the timeframe
> given.

2.  All logs in AWS -- no impact on the network link (in case of a
    forensics

> investigation logs can be accessed).\
> NOTE: Though all the logs will be in AWS but not at one central
> location. Each app account will hold its respective logs.

3.  ArcSight ingestion is not in place. Integration through SNS or
    directly with CloudWatch would need to be worked out with most of
    effort on VHA side.

4.  Any additional logs to be captured need to be defined by VHA.

#  {#section-2 .•Table-Heading}

# Design Proposal {#design-proposal .•Table-Heading}

The following diagram provides a high-level overview of how ArcSight
provides a scalable architectures to support various Threat Detection
and Compliance requirements.

<!-- IMAGE: image-002 | {{caption}} -->{width="4.6816557305336834in"
height="2.1477220034995628in"}

Figure: ArcSight Architecture options.

The following diagram provides a high-level overview of how ArcSight
SmartConnector supports Amazon Web Services; CloudWatch, CloudTrail, S3
and Security Hub data sources.

\[customer\] Threat Detection is supported by NTT for afterhours triage
is supported.

<!-- IMAGE: image-003 | {{caption}} -->{width="4.536713692038496in"
height="2.529199475065617in"}

Figure: AWS Threat Detection High level option

The following diagram provides a high-level overview of how the AWS
Security Hub, CloudWatch connector collects and sends events through to
an ArcSight destination.

<!-- IMAGE: image-004 | {{caption}} -->{width="6.768055555555556in" height="3.3875in"}

Figure: Conceptual - ArcSight SmartConnector AWS Configuration

<!-- IMAGE: image-005 | {{caption}} -->{width="6.768055555555556in"
height="2.6347222222222224in"}

Figure: AWS Security Monitoring Data flow

Figure: Conceptual Diagram -- ArcSight SmartConnector for Windows Event
Log Forwarding and Linux (rsyslog.)

Limits and maximums

-   Please be aware of service AWS service limitations of all AWS native
    security services.

-   AWS SecurityHub service limits;

    -   <https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub_limits.html>

-   AWS CloudWatch service limits;

    -   <https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html>

-   ArcSight SmartConnector for AWS SecurityHub supports AWS GuardDuty
    at the time of writing.
    <https://community.microfocus.com/t5/ArcSight-Connectors/SmartConnector-for-Amazon-Web-Services-Security-Hub/ta-p/2814565>

```{=html}
<!-- -->
```
-   GuardDuty Default

-   GuardDuty AWS_API_CALL

-   GuardDuty DNS_REQUEST

-   GuardDuty NETWORK_CONNECTION GuardDuty PORT_PROBE

-   Resource Header ResourcesDetailsAwsEc2Instance 

-   ResourcesDetailsAwsIamAccessKey 

-   ResourcesDetailsAwsEc2NetworkInterface

-   ResourcesDetailsAwsEc2SecurityGroup 

-   ResourcesDetailsAwsIamRole 

-   ResourcesDetailsAwsKmsKey 

-   ResourcesDetailsAwsS3Bucket ResourcesDetailsAwsS3Object 

-   ResourcesDetailsAwsSnsTopic 

-   ResourcesDetailsAwsSqsQueue 

-   ResourcesDetailsAwsLambdaFunction

Assumptions

-   \[customer\] will configure all data sources to appropriate native
    AWS logging services.

-   AWS Guard Duty, IAM, CloudTrail, CloudWatch, SecurityHub configured
    to send logs into corresponding collectors.

-   2000 EPS maximum per Smart Connector.

-   \[customer\] will utilize existing on-prem ESM/Logger platform for
    Compliance and Threat Detection.

-   Aggregations and Correlation will occur on AWS side to reduce
    bandwidth.

-   SmartConnectors will forward logs into on-premise ArcSight Logger
    and ESM.

-   \[customer\] will need to develop a network design model as part of
    the design.

-   Applications, Operating Systems (Linux and Windows) will be
    monitored by ArcSight SmartConnector for Windows/Windows sysmon and
    Linux, using Windows Event Forward and rsyslogd.

    -   <https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/configuring_basic_system_settings/configuring-a-remote-logging-solution_configuring-basic-system-settings>

    -   <https://docs.microsoft.com/en-us/windows/security/threat-protection/use-windows-event-forwarding-to-assist-in-intrusion-detection>

-   \[customer\] will deploy CloudWatch agents on all OS.

    -   <https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/install-CloudWatch-Agent-on-EC2-Instance.html>

# Sizing figures (rule of thumb)  {#sizing-figures-rule-of-thumb .•Table-Heading}

CPU

-   In general, ESM system with \"fewer but faster CPU cores\" will have
    much better performance than a system with \"more but slower CPU
    cores\"

-   i.e. Select the CPU with highest clock freq. (i.e. 16 Cores@3GHz
    system is much faster than 24Cores@2GHz)

ESM Memory

-   In general, propose 128GB (256GB would be better)

Storage  

Recommend to allocate at least:

-   \- 1  IOPS  per 6 events (just for event insertion, Concurrent
    access:  rare       Content Workload: lite     Report Generation:
     rare)

-   \- 1 to 2 IOPS per events (Small deployment, Concurrent access:
     Lite        Content Workload: lite - medium     Report Generation:
     Lite )

-   \- 4+  IOPS per events  (Normal SOC, Concurrent access:  1-2    
    Content Workload: Medium,    Report Generation: Lite to­ Medium)

-   \- 7+  IOPS per events (MSSP environment, Concurrent Access: 3-4,
     Content Workload: Medium,    Report Generation: Medium) 

Connector Sizing

-   Allocate two physical CPU cores for OS

-   Reserve 256MB of memory per physical CPU core as OS overhead (I.e.
    for a system with 16 physical CPU core, reserve 4GB of RAM as OS
    overhead)

-   Allocate one physical CPU core per Connecter

-   Allocate at least 1GB RAM per Windows Unified Connector, 512Mb or
    more for other types of Connector

-   Each Windows Unified Connector (WUC) supports a max of 200-300 hosts
    at 1 eps or 100 hosts at 3 eps or 6 hosts at 50 eps.

-   Running not more than 12 Connectors per Server.

-   For each Connector, reserve 1GB of storage for application
    binaries + 1GB (or more, depends on the requirement) for Event
    Cache 

-   around 30% degrade in performance with one additional ESM
    destination 

-   one syslog connector can support up to 2500 EPS (post aggregated /
    filer-out event rate)

# Capacity Design - Traffic & Bandwidth  {#capacity-design---traffic-bandwidth .•Table-Heading}

To better understand the impact to the network that this project will
have, we need to equate events per second (EPS) with network bandwidth.
To do this we use the following equation:

**KB/Sec**=

**EPS** = Events per Second.

**Ps/1024** = Packet size expressed in Kilobytes

> Syslog packet sizes vary between 100 -- 500 bytes. For the
> calculations assume 400 bytes (0.39KB)
>
> CEF packets vary between 600 -- 1765 bytes. For the calculations
> assume 1400 bytes (1.37KB)

**Ar** = Aggregation Ratio. We assume an average aggregation ratio of
30%. Therefore Ar = 0.7.

**Fr** = Filtering Ratio. We assume that a further 5% of events are
filtered at the SmartConnectors. Therefore Fr = 0.95

**Cr** = Compression Ratio. The default compression ratio for the
Arcsight SmartMessaging protocol (used for communication between
Arcsight devices) is 9:1. It can go up to 20:1, but we use 9:1 as the
default. Therefore Cr = .or 0.1(repeating).

Symantec LCP devices do not support the SmartMessaging protocol. They do
support CEF packets. They typically reduce (compress) event information
by 10:1 for transmission to the Symantec SOC.

**KB/Sec=**

# Logger/ESM AWS Configuration {#loggeresm-aws-configuration .•Table-Heading}

The following information is provide for information purposes only,
\[customer\] has a existing on-prem environment that will be utlized

AWS

Because AWS provides configuration options, this section will be broken
down in each relevant category.

The AWS environment can be accessed through different methods: VPN, SSH
connection Forwarding, and directly through the internet. It is not
recommended to leave security systems with direct connections available
from the internet.

### VPCs

AWS provides a fairly complex system for managing your cloud network.
The system comes configured with acceptable defaults for simple
configurations primarily using resources in the same region and
availability zones.

Depending on what your current configuration is, talk with your AWS
Architect or Account Rep to understand how pricing may be impacted by
modifications here.

The VPCs and Subnets are directly related, with VPCs defining which DHCP
options CIDRs utilize. All ArcSight ESM components should be running in
the same Availability Zone, for example "us-east-2a".

You are free to add a name to your zones and modify the addresses if
needed. It is also possible to modify the auto-assignment of public ipv4
addresses.

Default VPC Configuration\
<!-- IMAGE: image-006 | {{caption}} -->{width="6.690277777777778in"
height="1.4902777777777778in"}

Default Subnet Configuration\
<!-- IMAGE: image-007 | {{caption}} -->{width="6.690277777777778in"
height="1.5798611111111112in"}

### Security Groups

Within VPCs or EC2, Security Groups can be configured. Security Groups
are firewall rules allowing accepting not only IP Addresses or Subnets
in CIDR notation, but also other Security Group IDs as source or
destination of rules. An AWS EC2 instance is assigned at least one
Security Group.

An AWS instance can be part of multiple Security Groups, allowing for
simple firewall additions to be added only to a portion of your
instances.

An initial configuration could be:

-   Security Group 1

    -   Outbound connections

        -   Accept all traffic to 0.0.0.0/0

    -   Inbound connections

        -   Accept all traffic from Security Group 1 ID as source

-   Security Group 2

    -   Outbound connections

        -   Accept all traffic to 0.0.0.0/0

    -   Inbound connections

        -   Accept SSH traffic from 0.0.0.0/0 (if not using VPN, exposes
            to internet)

        -   Accept TCP/8443 from 0.0.0.0/0 (if not using VPN, exposes to
            internet)

Multiple security
groups:<!-- IMAGE: image-008 | {{caption}} -->{width="6.6930555555555555in"
height="2.5027777777777778in"}

Inbound rule\
<!-- IMAGE: image-009 | {{caption}} -->{width="6.6930555555555555in"
height="1.6041666666666667in"}

Outbound rule - Internet allowed\
<!-- IMAGE: image-010 | {{caption}} -->{width="6.6930555555555555in"
height="1.6423611111111112in"}

### Route 53

AWS "Route 53" provides DNS resolution and can be used for both external
and internal domain resolution.

For our configuration, simple private DNS resolution was selected for
internal networking to work using hostnames. Because of AWS nature of
dynamic external IPs, it is the user's choice to connect via VPN or make
the same hostname available for direct connection on the internet. It is
not recommend running security systems, potentially with
business-critical information, exposed to the internet.

Private DNS configuration\
<!-- IMAGE: image-011 | {{caption}} -->{width="6.6930555555555555in" height="1.44375in"}

Every time a new EC2 instance is created, they are assigned a new IP
address from the internal pool. The internal IP Address is always fixed
between instance restarts and can be configured directly into the Route
53 section.

It is possible to use an A record alias when quick manual DNS
redirection is needed.

Sample DNS Entries\
<!-- IMAGE: image-012 | {{caption}} -->{width="6.6930555555555555in"
height="3.5166666666666666in"}

### EC2 -- Key Pair

This step is optional but allows you to import a public portion of an
owned Key Pair for authentication purposes. This is found under EC2 --
Key Pairs.

In case a key pair isn't imported, EC2 can create one and make it
available for download before starting the instance during [[\'Step
7\' - Review]{.underline}](#review)

Sample RSA Public Key\
<!-- IMAGE: image-013 | {{caption}} -->{width="6.690277777777778in"
height="3.770138888888889in"}

### EC2

One of the most important services provided by AWS, Amazon **E**lastic
**C**ompute **C**loud provides virtual or bare-metal servers for
customers. Although ArcSight ESM can be installed in a variety of
configurations, depending on the EPS target, it is important to observe
that ArcSight ESM:

-   heavily relies on multi-threading to achieve high EPS

-   can benefit more from CPUs with better IPC (instructions per clock)

    -   Newer CPUs usually have IPC improvements

-   is extremely dependent on Disk IO and will require EBS-Optimized
    instances

    -   This provides a dedicated high-speed connection to storage

    -   A mix of disks are required to achieve optimal configuration,
        especially in distributed mode systems.

-   benefits from hyper-threading!

    -   Hyper-threading can be an issue if all threads are working above
        75% CPU. Because of how hyper-threading works, this can add more
        delays. In cases with 100% CPU utilization in a specific core,
        the sibling (or HT core) will introduce delays. It is possible
        to dynamically disable HT within the Linux system until the
        content can be identified. Note that, usually, MySQL utilizing
        100% of a single core doesn't impact EPS.

-   may benefit more from higher frequency CPUs than from a higher
    number of threads

    -   this can be true for systems running in compact mode with heavy
        rules, reaching 100% CPU utilization. EC2 has offers from 2.5Ghz
        to 3.0Ghz utilizing the newer Intel Xeon CPUs (usually 5% or
        more faster than the older Xeon E3 line).

    -   AMD CPUs have not been considered in this guide because they are
        slightly slower in frequency when compared to Intel CPUs as well
        as having slightly weaker IPC capabilities and increased memory
        latency.

    -   It is also not recommended to run older versions of Intel CPUs
        as they tend to be more expensive and slower.

The installation on EC2 is fairly straightforward. For more complex
environments, check with your AWS Architect on how to configure your
specific environment.

The AWS configuration for both Compact and Distributed modes are
similar. ArcSight ESM in Compact mode is usually limited by heavy
content. When that is the case, the system is expected to work close to
22k\~25k EPS.

When content is fine-tuned, with rules and datamonitors being very
specific about the events they process and, in some cases, splitting a
rule functionality in two, reducing the number of events each individual
rule processes, it is possible to go past the 25k EPS mark.

#### Choose AMI

CentOS 7.6 was utilized for this installation, but RedHat 7.6 can also
be used.

The specific version selected is "CentOS 7 (x86_64) - with Updates HVM"
and can be found here:
[[https://aws.amazon.com/marketplace/pp]{.underline}[/B00O7WM7QW]{.underline}](https://aws.amazon.com/marketplace/pp/B00O7WM7QW)

After selecting "Launch instance" in the EC2 menu, you will be required
to select the Image to use during 'Step 1':

Step1: AMI Selection\
<!-- IMAGE: image-014 | {{caption}} -->{width="6.6930555555555555in"
height="1.7361111111111112in"}

#### Choose Instance Type

Step 2 will require us to choose an instance type.

These are the preferred instance types for ArcSight ESM to run:

  ------------------ -------------- --------------------- -------------------
  EC2 Instance Type  ESM Compact    ESM Distributed       ESM Distributed
                                    Persistor             Nodes

  **m5.12xlarge**    **yes**        **yes\*\***           **yes\*\*\***

  **m5.24xlarge**    **yes\***      **yes**               **yes\*\*\***

  **c5n.9xlarge**    **yes**        **no**                **no**

  **c5n.18xlarge**   **yes**        **yes\*\***           **no**

  **r5.12xlarge**    **no**         **no**                **yes**

  **r5.24xlarge**    **no**         **no**                **yes\*\*\***
  ------------------ -------------- --------------------- -------------------

\* This configuration may not adequately support ESM in compact mode
with higher EPS because the issue is usually related to single thread
event flow in rules and datamonitors. It is possible to benefit more
from a larger instance if the "metrics system" doesn't show single
thread contention.

\*\* Using these alternative configurations can provide some benefits to
the system depending on the desired EPS. Because of how easy it is to
change servers on AWS, it is recommended to test how it behaves in your
environment. These configurations may suffer from some form of
degradation depending on how many Active Channels and Reports are
running in the background.

\*\*\* mbus_data services can benefit from having more memory available
and avoiding reading from the disk whenever possible. Depending on EPS,
different configurations will suffice, but we recommend the servers with
more memory available to avoid reading from disks whenever possible by
automatically leveraging Linux memory caching.

Pay attention to not select some of the other options for c5n, for
example the ones called only "c5" (no 'n') as these have less memory
available or c4 (older CPU generations). The same is true for other
variations of the m5 servers, with 'a' or 'd' suffixes as one is the AMD
variant (first iteration of EPYC servers) and the other provides local
NVME SSD storage (not needed).

Step 2: Instance Type\
<!-- IMAGE: image-015 | {{caption}} -->{width="6.6930555555555555in"
height="0.8083333333333333in"}

#### Configure Instance

Some options in 'Step 3' may impact billing. Check with your AWS
Architect on the impact of these options.

It is not recommended to use Spot Instances as there are no guarantees
an instance will be available and this can bring the whole system down.

ArcSight ESM also won't support Auto Scaling Groups. Other options like
Placement groups, Capacity Reservation, IAM role, shutdown behavior,
Enable termination protection, Monitoring, Tenancy and Elastic Inference
play minor administrative roles and a few of them may impact pricing.

For the deployment of ArcSight ESM, it is important that all nodes are
localized not only in the same region but also in the same availability
zone. The previous configuration of Network and Subnets (configured in
[[VPCs]{.underline}](#vpcs)) is available for selection now.

By default, the subnet will be auto assigned a Public IP address,
assuming the server only has one network interface configured. This
Public IP Address changes with every instance Stop/Start.

Step 3: Network Snippet\
<!-- IMAGE: image-016 | {{caption}} -->{width="6.6930555555555555in" height="1.1375in"}

For advanced Cloud Configurations, it is possible to use the Advanced
Details tab to automate your Linux configuration.

#### Add Storage

AWS EBS has a few different types of Storage to select from. ArcSight
ESM works properly when using gp2 (General Purpose SSD) and io1
(Provisioned IOPS SSD) storage types.

It is extremely important to understand how EBS works. It is network
storage that appears, inside the OS, as a NVME Disk when using
EBS-Optimized instances. The EBS-Optimized instances have an extra
10Gbps network card that is exclusively used for Disk connection. This
limits the maximum throughput of the system to 1,780 Mbps. Even though
it says NVME disk, behind the scenes EBS is providing several disks to
store your data, with redundancies and snapshots available.

There are still other factors limiting how much performance we can have
on each type of Disk. GP2 disks have a limited amount of IOPs they will
provide but are able to burst for short times. IO1 disks provide
guaranteed IOPs.

GP2 disks provide a maximum of 250 Mb/s throughput, but that is only
achievable in a sustained format when the provisioned disk has more than
**334 Gb** of disk space. Anything below that is subject to other limits
but can burst for short time.

Both disks will keep latency to a minimum when working below capacity.

In both cases, AWS Disk performance is directly linked to modifying at
least one configuration later on inside the OS: read head.

Because AWS is very reliable, it is possible to not utilize RAID
systems. RAID-5/6 or other variants are not supported. Any sort of
mirroring will use extra disk resources and consume from the total
10Gbps bandwidth available. In some cases, it is cheaper to use multiple
GP2 disks of at least **334 Gb** and leverage RAID-0 configuration (this
can be used for archives and mbus_data).

Another important detail, storage can be the most expensive portion of
an EC2 deployment, especially when talking about large amount of data
and snapshots.

The following table will help you allocate the proper resources for OS,
with the only changing portion being the Disk Size for ArcSight Data and
if required additional Storage for archives. Keep in mind Storage
requirements are directly linked to your needs of Online Retention or
Retention available through archives, and EPS. On a system with 400k
EPS, 4TB may not be enough to store 1 day of data.

+---------------+-------------+--------------------+------------------+
| **Partition   | **ESM       | **ESM Distributed  | **ESM            |
| Type\         | Compact**   | Persistor**        | Distributed      |
| Mount Point** |             |                    | Nodes**          |
+---------------+-------------+--------------------+------------------+
| **OS Disk\    | **80GB\     | **80GB\            | **80GB\          |
| /**           | gp2**       | gp2**              | gp2**            |
+---------------+-------------+--------------------+------------------+
| **arcsight    | **3TB+**    | **3TB+**           | **500GB**        |
| data\         |             |                    |                  |
| /o            | **io1 --    | **io1 -- 4000+     | **gp2**          |
| pt/arcsight** | 4000 IOPS** | IOPS**             |                  |
+---------------+-------------+--------------------+------------------+
| **mbus data\  | **-**       | **-**              | **3x350GB gp2    |
| /op           |             |                    | RAID-0\          |
| t/mbus_data** |             |                    | 1x1.1TB io1 3000 |
|               |             |                    | IOPS**           |
+---------------+-------------+--------------------+------------------+
| **Archives**  | **350GB+    | **350GB+ gp2**     | **-**            |
|               | gp2**       |                    |                  |
| **/opt/bkp**  |             | **io1 1000+ IOPS** |                  |
|               | **io1 1000+ |                    |                  |
|               | IOPS**      |                    |                  |
+---------------+-------------+--------------------+------------------+

It is also possible to select encryption of disks during this step, if
desired.

Step 4: Add Storage (ESM Compact/Persistor)\
<!-- IMAGE: image-031 | {{caption}} -->{width="6.690277777777778in"
height="1.1597222222222223in"}

Step 4: Add Storage (Distributed Node)\
<!-- IMAGE: image-017 | {{caption}} -->{width="6.690277777777778in" height="1.5in"}

#### Add Tags

Tags are used when organizing or automating installations.

The usage of tags is not necessary for the deployment of ArcSight ESM,
but can be something your company a usage policy requires. Verify with
your AWS Architect.

#### Configure Security Group

Depending on your existing Security Groups or the creation of new ones,
your needs here may be different.

By default, everything is blocking and allowed connections needs to be
specifically allowed. Multiple Security Groups can be selected.

Step 6: Security Groups\
<!-- IMAGE: image-018 | {{caption}} -->{width="6.6930555555555555in"
height="1.726388888888889in"}

#### Review

The last Step, 7, only requires you to review your choices and confirm
them.

Before launching the instance, you will be asked to select a Key pair to
connect via ssh. Every AMI works differently here: CentOS AMI will allow
you to use the select key pair to connect as the user centos, which can
perform sudo commands without passwords (this is the preferred way).

Step 7: Creating new Key Pair after Review\
<!-- IMAGE: image-019 | {{caption}} -->{width="6.690277777777778in"
height="4.979861111111111in"}

## Linux

As soon as the server is working

The Linux server configuration requires multiple steps. While regular
Linux administrative tasks may be mentioned, they will not be detailed.

Important Note:

If any of the servers used have SSH exposed to the internet, it is
recommended that password authentications are ***disabled***.

All users needing remote connection should be assigned ssh keys (at
least one is needed during instance deployment) and sudo without
password should be provided for users needing higher privileges.

### Disk IO

Disk IO on AWS requires specific tuning of Read Ahead and also benefits
from a better scheduler.

In some AWS documents, it is possible to find references for 2048 as the
read-ahead value, but AWS automatically converts it to 4096 in newer
disks. This raises the maximum read speed from 12MB/s to the maximum for
each disk type.

The scheduler selected, updated from the default none, is mq-deadline;
this will also be the new default on RedHat/CentOS 8.x. This
configuration helps the system decides how to better handle IO when
sending several requests together.

Considering disks can be plugged with the system running, the preferred
method to adjusting these parameters is through udev.

When connected as root, the following command can be used to automate
this process:

cat \<\<EOF \> /etc/udev/rules.d/20-diskio.rules

SUBSYSTEM==\"block\", ACTION==\"add\|change\",
KERNEL==\"md\[0-9\]\*\|dm\[0-9\]\*\|nvme\[0-9\]\*n1\",
ATTR{bdi/read_ahead_kb}=\"2048\", ATTR{queue/scheduler}=\"mq-deadline\"

EOF

udevadm trigger

### Extra Packages

This is a list of commands to install extra packages that are required
for different ArcSight components or that were instrumental in
identifying server and connection issues.

yum -y update

yum -y upgrade

yum -y install lvm2 zip unzip xev xauth fontconfig dejavu-sans-fonts
mdadm bind-utils psmisc pciutils lsof sysstat

### Filesystem Configurations

Both ext4 and xfs are supported. During several weeks of testing and
validating configurations, both systems have been within 3% of their
target EPS, with ext4 usually coming out ahead.

Ext4 also tends to flush data in batches in a few scenarios while xfs
writes constantly to the disk, possibly alleviating bottlenecks.

Also, another interesting factor before deciding which filesystem to use
is that ext4 filesystems tend to concentrate more IO waiting in a single
thread, while xfs behaves more multi-threaded. The reason for xfs
possibly being slightly behind the EPS measurement can be extra thread
manipulation overhead.

For systems with constant high load, xfs can be a better option as the
processing is more distributed but there is no big performance gap.

By default, the OS partition is always of xfs on CentOS 7.6. The EBS
storage also has a special configuration on AWS and is assigned as
/dev/sda1 instead of /dev/sda in AWS configuration panel.

Xfs partitions cannot be shrunk. If shrinking partitions in the future
is needed or desired, use ext4.

### Partitions

All disks, with the exception of OS Disk, have been configured to use
LVM. The LVM Physical Volume was assigned to a partition instead of a
whole disk, /dev/nvme1n1p1 instead of /dev/nvme1n1, for example.

With multiple disks, there's no guarantee they will be attached in the
same place after reboot, so it is absolutely needed to use UUID in
/etc/fstab.

The next few sections will include scripts to create these. They all
require the arcsight user to be created:

useradd -m arcsight

Using LVM provided small benefits: in some cases, IO was better
aggregated when going through LVM first then to "NVME" device.

#### Compact/Persistor

Two options are offered for /opt/arcsight using LVM: ext4 or xfs

##### /opt/arcsight

###### ext4

parted -s -a opt /dev/nvme1n1 mklabel gpt

parted -s -a opt /dev/nvme1n1 mkpart primary ext4 0% 100%

parted -s -a opt /dev/nvme1n1 set 1 lvm on

pvcreate /dev/nvme1n1p1

vgcreate arst /dev/nvme1n1p1

lvcreate -L 100%FREE arst -n data

mkfs.ext4 -m0 -b 4096 /dev/disk/by-id/dm-name-arst-data

blkid \| sed \'s/\"//g\' \| awk \'/arst-data/ {print \$2\" /opt/arcsight
ext4 defaults 0 0\"}\' \>\> /etc/fstab

mkdir /opt/arcsight

mount -a

chown -R arcsight:arcsight /opt/arcsight

###### xfs

parted -s -a opt /dev/nvme1n1 mklabel gpt

parted -s -a opt /dev/nvme1n1 mkpart primary ext4 0% 100%

parted -s -a opt /dev/nvme1n1 set 1 lvm on

pvcreate /dev/nvme1n1p1

vgcreate arst /dev/nvme1n1p1

lvcreate -L 100%FREE arst -n data

mkfs.xfs -b size=4096 /dev/disk/by-id/dm-name-arst-data

blkid \| sed \'s/\"//g\' \| awk \'/arst-data/ {print \$2\" /opt/arcsight
xfs defaults 0 0\"}\' \>\> /etc/fstab

mkdir /opt/arcsight

mount -a

chown -R arcsight:arcsight /opt/arcsight

#### Distributed Nodes

Distributed Nodes are more complex because they also require mbus_data
(Local Kafka) storage.

Because of how disks are allocated on AWS, we can't expect /dev/nvme1n1
to be the larger disk reserved to /opt/arcsight. If using the suggested
value of 500GB the next sections will work for ext4 or xfs

##### /opt/arcsight

###### ext4

\# Node data

i=\$(lsblk -pd \| awk \'/500G/ {print \$1}\')

parted -s -a opt \$i mklabel gpt

parted -s -a opt \$i mkpart primary ext4 0% 100%

parted -s -a opt \$i set 1 lvm on

pvcreate \${i}p1

vgcreate arst \${i}p1

lvcreate -l 100%FREE arst -n data

mkfs.ext4 -m0 -b 4096 /dev/disk/by-id/dm-name-arst-data

blkid \| sed \'s/\"//g\' \| awk \'/arst-data/ {print \$2\" /opt/arcsight
ext4 defaults 0 0\"}\' \>\> /etc/fstab

###### xfs

\# Node data

i=\$(lsblk -pd \| awk \'/500G/ {print \$1}\')

parted -s -a opt \$i mklabel gpt

parted -s -a opt \$i mkpart primary ext4 0% 100%

parted -s -a opt \$i set 1 lvm on

pvcreate \${i}p1

vgcreate arst \${i}p1

lvcreate -l 100%FREE arst -n data

mkfs.xfs -b size=4096 /dev/disk/by-id/dm-name-arst-data

blkid \| sed \'s/\"//g\' \| awk \'/arst-data/ {print \$2\" /opt/arcsight
xfs defaults 0 0\"}\' \>\> /etc/fstab

##### /opt/mbus_data

There are two options for configuring mbus_data: using RAID-0 with gp2
disks or regular LVM with io1 disks.

When using RAID-0 with 3 disks, the raid and filesystem creation require
extra arguments to ensure proper alignment of IOs.

The examples here are only for RAID-0.

With ESM 7.0 Patch 2, after configuring mbus_data service but before
starting it, an extra script needs to be executed. This script maps the
mbus_data ESM directory to /opt/mbus_data, separating that IO from other
internal processes.

###### RAID-0 - ext4

\# Kafka Data

for i in \$(lsblk -pd \| awk \'/350G/ {print \$1}\'); do

parted -s -a opt \$i mklabel gpt

parted -s -a opt \$i mkpart primary ext4 0% 100%

parted -s -a opt \$i set 1 raid on

done

i=(\$(lsblk -pd \| awk \'/350G/ {print \$1\"p1\"}\'))

mdadm \--create /dev/md0 \--level=0 -c 96 \--raid-devices=3 \${i\[@\]}

mkfs.ext4 -m0 -b 4096 -E stride=24,stripe-width=72 /dev/md0

blkid \| sed \'s/\"//g\' \| awk \'/md0:/ {print \$2\" /opt/mbus_data
ext4 defaults 0 0\"}\' \>\> /etc/fstab

###### RAID-0 - xfs

\# Kafka Data

for i in \$(lsblk -pd \| awk \'/350G/ {print \$1}\'); do

parted -s -a opt \$i mklabel gpt

parted -s -a opt \$i mkpart primary ext4 0% 100%

parted -s -a opt \$i set 1 raid on

done

i=(\$(lsblk -pd \| awk \'/350G/ {print \$1\"p1\"}\'))

mdadm \--create /dev/md0 \--level=0 -c 96 \--raid-devices=3 \${i\[@\]}

mkfs.xfs -b size=4096 -d su=96k,sw=3 /dev/md0

blkid \| sed \'s/\"//g\' \| awk \'/md0:/ {print \$2\" /opt/mbus_data xfs
defaults 0 0\"}\' \>\> /etc/fstab

### Hostname

The hostname can be configured in different places. Considering AWS uses
cloud-init, configuration can be automated before the server is even
started or by customizing the cloud-init file.

/etc/cloud/cloud.cfd.d/01_hostname.cfg

hostname: myhost

fqdn: myhost.my.full.domain

### ArcSight ESM

An extra configuration needed for ArcSight ESM 7.0 Patch 1 (base
installer required to apply Patch 2) is modifying the OS release version
to simulate an older and supported version.

/etc/redhat-release

CentOS Linux release 7.4.1810 (Core)

By having the version changed from 7.***6***.1810 to 7.***4***.1810 the
installer verification will bypass the OS version and work.

The current ArcSight ESM version does not support installations with
RedHat or CentOS 8.x. Going from 7.4 to 7.6 is a minor OS update and,
with a few exceptions, usually about security updates.

### Distributed Node -- mbus_data

To properly segregate mbus_data IO from OS and other ArcSight services,
mbus_data has to be linked with the previously created directory
/opt/mbus_data.

This configuration happens ***after*** mbus_data is installed.

The following script expects the source directory to be at
'/opt/arcsight/var/data/' and the dedicated IO filesystem to be mounted
at '/opt/mbus_data'.

#!/bin/bash

SRC=\"/opt/arcsight/var/data/\"

DST=\"/opt/mbus_data\"

function unlinkAllMbusData() {

DIRS=(\$(find \"\$SRC\" -type l -name mbus_data\\\*))

for dir in \${DIRS\[@\]}; do

echo rm \"\$dir\"

rm \"\$dir\"

echo mv \"\$DST/\$(basename \"\$dir\")\" \"\$SRC\"

mv \"\$DST/\$(basename \"\$dir\")\" \"\$SRC\"

done

}

function linkAllMbusData() {

DIRS=(\$(find \"\$SRC\" -type d -name mbus_data\\\*))

for dir in \${DIRS\[@\]}; do

echo mv \"\$dir\" \"\$DST\"

mv \"\$dir\" \"\$DST\"

echo ln -s \"\$DST/\$(basename \"\$dir\")/\" \"\$SRC\"

ln -s \"\$DST/\$(basename \"\$dir\")\" \"\$SRC\"

done

}

echo
\"\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\"

echo -en \"Linking mbus_data\* directories\\n\"

echo -en \"from \\\"\$SRC\\\"\\n\"

echo -en \"to \\\"\$DST\\\"\\n\"

echo
\"\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\"

while true; do

read -p \"Type in e to enable or d disable links to dedicated disk or q
to quit \[e/d/q\] ?\" ed

case \$ed in

\[Ee\]\* ) linkAllMbusData; break;;

\[Dd\]\* ) unlinkAllMbusData; exit;;

\[Qq\]\* ) exit;;

\* ) echo \"Please answer e for enable or d to disable mbus_data linked
directories.\";;

esac

done

Create a file with this content in the Distributed Node and execute it
after mbus_data has been configured in the server.

Alternatively, instead of running the script, the directories can be
manually linked. From '/opt/arcsight/var/data' move the 'mbus_data??',
where '??" is the service number, to '/opt/mbus_data/'. For example, if
the mbus_data service where numbered 1 the command would be:

cd /opt/arcsight/var/data

mv mbus_data10 /opt/mbus_data

ln -s /opt/mbus_data/mbus_data10 mbus_data10

### Hyper threading

Different from current recommendations for "Hyper-thread disabled" in
the system BIOS (or during AWS provisioning), Hyper-thread should be
enabled to achieve higher EPS scenarios.

Hyper-thread is a technology where almost the entirety of one physical
core is shared between two virtual cores, also known as siblings. This
technology speeds up the processing of several processes by making a few
isolated processes take longer to run.

This effect is less noticed when a process doesn't use 100% of CPU time
as the basis for Hyper-threading is to benefit from idle CPU cycles in a
core to run other activities.

When ArcSight ESM utilization is under heavy load by content, rules and
datamonitors (applicable to compact mode and distributed nodes), this
may affect the overall performance of the server. As a solution,
hyper-threading can be dynamically disabled until the resource using too
much CPU time is under control.

For some cases, it may be preferred to completely disable Hyper-thread
all the time.

Executing the script below will prompt the user to enable or disable
hyper-threading.

#!/bin/bash

HYPERTHREADING=1

function toggleHyperThreading() {

for CPU in /sys/devices/system/cpu/cpu\[0-9\]\*; do

CPUID=\`basename \$CPU \| cut -b4-\`

echo -en \"CPU: \$CPUID\\t\"

\[ -e \$CPU/online \] && echo \"1\" \> \$CPU/online

THREAD1=\`cat \$CPU/topology/thread_siblings_list \| cut -f1 -d,\`

if \[ \$CPUID = \$THREAD1 \]; then

echo \"-\> enable\"

\[ -e \$CPU/online \] && echo \"1\" \> \$CPU/online

else

if \[ \"\$HYPERTHREADING\" -eq \"0\" \]; then echo \"-\> disabled\";
else echo \"-\> enabled\"; fi

echo \"\$HYPERTHREADING\" \> \$CPU/online

fi

done

}

function enabled() {

echo -en \"Enabling HyperThreading\\n\"

HYPERTHREADING=1

toggleHyperThreading

}

function disabled() {

echo -en \"Disabling HyperThreading\\n\"

HYPERTHREADING=0

toggleHyperThreading

}

ONLINE=\$(cat /sys/devices/system/cpu/online)

OFFLINE=\$(cat /sys/devices/system/cpu/offline)

echo
\"\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\"

echo -en \"CPU\'s online: \$ONLINE\\t CPU\'s offline: \$OFFLINE\\n\"

echo
\"\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\"

while true; do

read -p \"Type in e to enable or d disable hyperThreading or q to quit
\[e/d/q\] ?\" ed

case \$ed in

\[Ee\]\* ) enabled; break;;

\[Dd\]\* ) disabled;exit;;

\[Qq\]\* ) exit;;

\* ) echo \"Please answer e for enable or d for disable
hyperThreading.\";;

esac

## ArcSight ESM

ArcSight ESM version 7.0 Patch 2 was used as a basis for this study and
guide. It contains several improvements when compared to 7.0 Patch 1,
specifically around event ingestion and system optimizations that are
not available on 7.0 Patch 1.

Note that when running in distributed mode, all nodes need to be running
on the same ESM version or errors will occur while the system appears to
still operate.

### Packer Optimization

ArcSight ESM 7.0 Patch 2 has an improvement for persisting events into
the database, but it has to be manually enabled. This is mostly relevant
in High EPS scenarios or when dealing with large events.

Add the following to '/opt/arcsight/manager/config/server.properties'

packer.chunk-split-optimization=true

### Ingestion Buffers

When receiving more than 80k EPS, tweaking of two internal ingestion
buffers helped push the EPS and reduce the server load.

Add the following to '/opt/arcsight/manager/config/server.properties'

queue.logger.pre-security-event-persistor.capacity=200000

queue.logger.start-of-flow.capacity=200000

### Manager Java Heap Size

Working with High EPS requires a higher memory usage. Usually, 64GB for
the heap size is enough (Compact/Distributed).

When going past 100k EPS, even in a system with no content deployed,
receiving events requires about 64GB of heap. If going past 200k EPS,
the Manager Heap Size should be set to 128GB. Regular garbage
collections will often occur frequently in misconfigured systems, every
second or less, and the system will act as if it were performing a Full
Garbage collection.

To increase the Heap Size past the regular values allowed during
installation edit '/opt/arcsight/manager/config/server.wrapper.conf'.

128GB

wrapper.java.initmemory=131072

wrapper.java.maxmemory=131072

64GB

wrapper.java.initmemory=65536

wrapper.java.maxmemory=65536

# Performance

ArcSight ESM runs very well in AWS. It has the added benefit of
performing upgrades to more powerful hardware with minimal downtime.

When monitoring ArcSight ESM, it is important to have a system capable
of collecting reliable server information every second and use the right
tools to identify bottlenecks. Ideally, this system will also keep a
history so it is possible to go back in time and do comparisons or
identify the system behavior in a specific date.

Through monitoring these metrics, it is possible to fine tune ArcSight
ESM and achieve maximum performance in AWS.

With ArcSight ESM 7.0 Patch 2, before tuning, Distributed Correlation
was running at 240k EPS.

After tuning, a virtualized m5.24xlarge instance as the persistor runs
stable at 360k EPS and can be pushed to constant 400k EPS, with peaks of
430k+ EPS.

Considering potential large number of correlations some customers may
need, this server should be reserved for running ESM at 250k EPS for
ingestion with room for 20% correlations, bringing the total to 300k EPS
while running Active Channels and Reports.

A system running m5.12xlarge can achieve half of that potential, and is
the preferred instance type for the persistor when aiming at 100k EPS
ingestion.

The type of trends, reports and active channels in use still have an
impact on ESM's ability to keep up with EPS. Rules and Datamonitors are
impacted different in a distributed system and, while they don't block
event flow, heavy rules can trigger **backpressure** and hold the event
flow. Because of a more powerful instance may be required to achieve
your EPS needs.

## CPU

In most environments, an aggregate of CPU utilization by all cores is
polled every few minutes and a graphic is generated.

This is a graphic quite commonly seen in ArcSight:

Average CPU Utilization\
<!-- IMAGE: image-020 | {{caption}} -->{width="6.6930555555555555in"
height="2.459722222222222in"}

From this graphic, most administrators assume the system is doing very
well and it has 20% free utilization.

The per core graphics utilization tells a very different story:

Per Core CPU User Utilization\
<!-- IMAGE: image-021 | {{caption}} -->{width="6.6930555555555555in"
height="2.4854166666666666in"}

Several CPUs are working at 100% utilization when other CPU utilization
metrics are factored in, like System and IO Wait, it is possible to
understand the system is at its maximum.

## Memory

Memory usage is usually constant on ArcSight ESM. Cached memory will
slowly increase by leveraging free space, speeding up recent disk
access.

Memory Utilization\
<!-- IMAGE: image-022 | {{caption}} -->{width="6.690277777777778in"
height="2.9430555555555555in"}

## Swap

Usually, swap should be avoided in the server. In a system correctly
configured, swap is never needed.

Swap is a "cheap" alternative to memory but, on AWS, the price of swap
is too high considering the limited disk bandwidth/IOPs.

System with no SWAP\
<!-- IMAGE: image-023 | {{caption}} -->{width="6.690277777777778in"
height="2.9097222222222223in"}

In systems where swap is configured, monitoring the current swap use is
important: it shouldn't grow unless the system is experiencing lack of
memory when the kernel vm.swappines is set to 0.

## Disk

Several metrics should be monitored on Disks.

### Disk IO/s (IOPs)

The amount of IOPs is very important in AWS as going past the
provisioned IOPs will result in EBS slowing down data flow to stay
within the provisioned limit.

When monitoring servers with multiple disks, it is important to observe
which Disk is in use and how it is being used by the OS.

Physical disks (nvme\*n1) are compared to virtual disks (dm-\*, md\*) to
verify possible discrepancies between their number. If the difference
between writes or reads for the same dataset is too big, the system may
be suffering from write amplification.

Healthy Disk IO/s\
<!-- IMAGE: image-024 | {{caption}} -->{width="6.690277777777778in"
height="2.979861111111111in"}

### Disk Throughput

Considering the same constant usage, Disk Throughput should be fairly
similar over a period of time. Big data spikes or huge gaps in the
metrics, that can't be attributed to a scheduled process, can be
indicators of problems.

Healthy Disk Throughput\
<!-- IMAGE: image-025 | {{caption}} -->{width="6.690277777777778in"
height="2.9902777777777776in"}

### Disk Utilization

Disk utilization is a simple metric that indicates for how long the disk
was busy. At 100%, the disk was executing IO operations all the time and
is at its limit, even if latency is low.

Disk Utilization %\
<!-- IMAGE: image-026 | {{caption}} -->{width="6.690277777777778in"
height="2.9902777777777776in"}

### Disk IO Time (Latency)

Probably the most important metric for ArcSight ESM in general. When
Disk IO Time, or Latency is high, Active Channels and EPS suffer.

Amazon EBS provides low latency Disk IO, even when under heavy load.
This is possible because EBS is simply allocating spaces in disks, but
using more sophisticated storage techniques and processing of IO.

Sub millisecond latency on Persistorin
PO<!-- IMAGE: image-027 | {{caption}} -->{width="6.690277777777778in"
height="2.970138888888889in"}

mbus_data (Kafka) under heavy load\
<!-- IMAGE: image-028 | {{caption}} -->{width="6.690277777777778in"
height="2.979861111111111in"}

### Disk Queue Depth (Avg)

The average Qeueue Depth, when measured every second, provides a very
good insight in how many IOs have been queued. The smaller this number,
the smaller is the requests waiting for IO.

Healthy Queue Depth\
<!-- IMAGE: image-029 | {{caption}} -->{width="6.690277777777778in"
height="2.959722222222222in"}

## Network

Network throughput should always be monitored to identify data spikes or
gaps and to ensure the current network bandwidth is always enough for
the system.

3.5Gbps required 400k EPS\
<!-- IMAGE: image-030 | {{caption}} -->{width="6.690277777777778in"
height="2.959722222222222in"}

# Final Remarks

Running ArcSight ESM on AWS is possible and enables customers to meet
high EPS requirements.

ArcSight ESM in Distributed mode is able to reach 250k ingestion EPS for
correlation. Depending on system utilization by rules, datamonitors, or
other resources possibly generating extra EPS, and resources using the
database like Active Channels, Reports and Trends, it is possible for
the EPS to reach numbers higher than 350k EPS.

The distributed mode configuration used to achieve these results is
should follow the Disk and OS guidelines provided by this document. The
internal services distribution should be:

Persistor Instance: m5.24xlarge, 1 x repo

Distributed Nodes 1 through 5: r5.12xlarge, 2 x Aggregators, 2 x
Correlators, 1 x DCache, 1 x mbus_data

Distributed Nodes 1 through 3: 1 x mbus_control

Distributed Nodes 1 through 2: 1 x repo

This configuration may achieve 400k+ EPS, but will be limited by the
current CPUs offered by AWS. When Active Channels, Reports, Trends and
other activities requiring CPU and IO are performed the EPS is ingestion
is impacted.

For most real-world scenarios, reaching 400k EPS should not be expected
when running under m5.24xlarge.

The different configurations available in AWS like better servers,
bigger disks, more IOPS, dedicated IOPS, snapshots, and others may incur
extra costs.

To understand exactly how the system is behaving an accurate and
frequent (down to the second) metrics system is needed.

This system should capture minor variations and provide granular
information without hiding data spikes.

By relying on precise metrics, it is possible to optimize AWS
configurations and costs while maintaining system requirements for
online data retention, archives and desired EPS.

# Reference material {#reference-material .•Table-Heading}

-   SANs AWS Threat Detection;

    -   <https://d1.awsstatic.com/Marketplace/solutions-center/downloads/Threat-detection-AWS-Marketplace-eBook.pdf>

-   Microfocus SmartConnector supported products;

    -   <https://www.microfocus.com/media/flyer/arcsight_connector_supported_products_flyer.pdf>

-   Microfocus SmartConnector Installations guide;

    -   <https://community.microfocus.com/t5/ArcSight-Connectors/ct-p/ConnectorsDocs>

-   Microfocus SmartConnector for Amazon Web Services CloudWatch;

    -   <https://community.microfocus.com/t5/ArcSight-Connectors/SmartConnector-for-Amazon-Web-Services-CloudWatch/ta-p/1684156>

-   Microfocus SmartConnector for Amazon Web Services CloudTrail;

    -   <https://community.microfocus.com/t5/ArcSight-Connectors/SmartConnector-for-Amazon-Web-Services-CloudTrail/ta-p/1583356?nm>

-   Microfocus SmartConnector for Amazon Web Services S3;

    -   <https://community.microfocus.com/t5/ArcSight-Connectors/SmartConnector-for-Amazon-Web-Services-S3/ta-p/2814564>

-   Microfocus SmartConnector for Amazon Web Services Security Hub;

    -   <https://community.microfocus.com/t5/ArcSight-Connectors/SmartConnector-for-Amazon-Web-Services-Security-Hub/ta-p/2814565>
