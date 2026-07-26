# Turnstone Setup

- https://forum.level1techs.com/t/dgx-spark-msi-edgexpert-and-cubi-nuc-agents-the-loop/252183
- https://www.youtube.com/watch?v=QPT4qqoze2U
- https://github.com/turnstonelabs/turnstone


```

 Turnstone is a great architecture because it allows you to have a library of models available whether they are running locally or in the cloud. 

You will need to utilize features like Personas that give instructions to the coordinator what to do, like analyzing if local development is stalled and to call for reinforcements by spawning a workstream that uses a cloud model to examine the situation and provide instructions. 

The coordinator still has some issues with stalling on occasion on my instance, but @eousphoros is a machine and has been making tons of improvements day over day so your feedback on if you run into stalls would be very helpful if you run into it.  My goal is to have my local cluster working 24/7 on my projects, personally.


, this fits into the turnstone coordinator pattern. If you have any questions, bugs, or feature requests; I am happy to help. I would suggest setting up an output guard llm, intent validation llm, and a ranker and either use tool policies or smart approvals for the workflow you described. (Smart approvals are disabled by default, output guard/intent validation llm can be the same model or a different one from the one driving the harness

```
