---
title: "Prelude on the Dynamics of a RR Robot"
date: 2025-11-30T07:02:25-05:00
description: Generic description
categories: ["Tutorial"]
tags: ["serial-kinematic robot", "dynamics", "inverse problem", "model-based", "symbolic"]
toc: true
math: false
draft: false
---




Before I derive and present the inverse dynamics of a RR robot in symbolic form for a future blog post, I want to discuss some parts before the main post.
In particular, I want to hint on the effort-flow concept and touch on some adjacent questions: why inverse and not forward, what is the benefit of using the effort-flow concept, why using different spaces, how to solve the dynamics equations, among other questions.

The result of the inverse dynamics is a set of equations that relates effort quantities to flow quantities. 
An effort quantity relates to forces, whereas a flow quantity relates to a velocity.
By flow quantities, I include their integral and their derivatives.
For the effort quantities, I do not include their integral and time derivatives, because I consider an inverse relation. 
It is a bit long-winded, but putting it in this way, we can acknowledge that there is more to it.
A more common statement is that the dynamics relates general forces to position, velocity, and acceleration.
By general forces, I mean forces (due to a translational motion) and torques, which can be seen angular forces due to a rotational motion.

Regarding the inverse relation, let us consider kinematics.
For some reason, it is common to say that forward kinematic provides the pose for given joint values.
On the other hand, the inverse kinematic provides the joint values for a given pose.
It makes sense if we realize that the joint values are element of the joint space, which is the robot's "own space."
The pose is an element of the Task space, which is a shared space, _e.g._, a space shared by the robot and its environment (with other human and robots).
More to that in a future post.
Back to the dynamics.
The case for the forward and inverse dynamics is not that straightforward, but a similar case can be made--A job for future me.
For some reason, the forward dynamics take the form of
$$
\begin{align}
X_\text{flow} = 
f\left( \int X_\text{effort} \ \mathrm{d}t, X_\text{effort}, \dfrac{\mathrm{d}}{\mathrm{d}t} X_\text{effort} \right)
,
\end{align}
$$
where effort and flow quantities are used.
So, it is in some sense Eq.(1) describes the general case.
Therefore, the inverse dynamics take the form of 
$$
\begin{align}
X_\text{effort} = 
g\left( \int X_\text{flow} \ \mathrm{d}t, X_\text{flow}, \dfrac{\mathrm{d}}{\mathrm{d}t} X_\text{flow} \right)
.
\end{align}
$$
Both, forward dynamics stated in Eq.(1) and inverse dynamics stated in Eq.(2), can be considered as the expression, when using the effort-flow concept.
I note that both expressions are not a standard way to introduce the dynamics.
I don't recall seeing those in a robotic textbook.


In robotics, the inverse dynamics stated in Eq.(2) is often expressed as 
$$
\begin{align}
\boldsymbol{M}\left(\boldsymbol{q}\right) \ddot{\boldsymbol{q}} +
\boldsymbol{C}\left(\boldsymbol{q}, \dot{\boldsymbol{q}}\right) \dot{\boldsymbol{q}} +
\boldsymbol{g}\left(\boldsymbol{q}\right) =
\boldsymbol{\tau}
,
\end{align}
$$
where
$$
\begin{align}
X_\text{effort} &= \boldsymbol{\tau}, \nonumber \\\\
\int X_\text{flow} \ \mathrm{d}t &= \boldsymbol{q}, \nonumber \\\\
X_\text{flow} &= \dot{\boldsymbol{q}}, \quad\text{and}\nonumber \\\\
\dfrac{\mathrm{d}}{\mathrm{d}t} X_\text{flow} &= \ddot{\boldsymbol{q}} \nonumber
\end{align}
$$
in my notation stated in Eq.(2).
This equation, _i.e._, Eq.(3), is usually solved to obtain the motion of the robot, _i.e._, given the general forces as input, get the resulting $\boldsymbol{q}$, $\dot{\boldsymbol{q}}$, and $\ddot{\boldsymbol{q}}$ causing the motion of the robot.
If we are interested in solving Eq.(2), we would not try to get Eq.(1).
Most certainly not.
In general, the set of equations in Eq.(3) is a set of coupled, non-linear differential equations that is impossible to solve in a closed-form fashion.
Exceptions to this are robots with a trivial morphology.

Instead of deriving Eq.(1), inverse dynamic stated in Eq.(3) is solved though integration.
One common approach is rearranging Eq.(3) and then integrating $\ddot{\boldsymbol{q}}$, which result in
$$
\begin{align}
\ddot{\boldsymbol{q}} &=
\boldsymbol{M}^{-1}\left(\boldsymbol{q}\right) 
\left(
\boldsymbol{\tau} - 
\boldsymbol{C}\left(\boldsymbol{q}, \dot{\boldsymbol{q}}\right) \dot{\boldsymbol{q}} -
\boldsymbol{g}\left(\boldsymbol{q}\right)
\right) \nonumber \\\\
\dot{\boldsymbol{q}} &= \int \ddot{\boldsymbol{q}} \ \mathrm{d}t, \quad\text{and}\nonumber \\\\
\boldsymbol{q} &= \int \dot{\boldsymbol{q}} \ \mathrm{d}t.  \nonumber
\end{align}
$$
This double integrator utilizing the [simple Forward Euler method](https://en.wikipedia.org/wiki/Euler_method) is sufficient. 
The integration steps are small considering a control frequency of $1000\ \text{Hz}$.
Moreover, the resulting error due to the integration will be ironed by the controller.
More importantly, the inverse dynamics stated in Eq.(3) is not the "correct" inverse dynamics equation of a robot.

[_"All models are wrong, but some are useful."_](https://en.wikipedia.org/wiki/All_models_are_wrong)
This is true for Eq.(3) as well.
In practice, we derive the full and complete inverse dynamics and then simplify them.
The non-simplified set of equation are very complicated and complex. 
This results in high computational load in exchange for a slightly better result.
For example, compared to Eq.(3),
$$
\begin{align}
\boldsymbol{M}\left(\boldsymbol{q}\right) \ddot{\boldsymbol{q}} +
\widetilde{\boldsymbol{C}}\left(\boldsymbol{q}, \dot{\boldsymbol{q}}\right) +
\boldsymbol{g}\left(\boldsymbol{q}\right) =
\boldsymbol{\tau}
\end{align}
$$
is a better approximation of the real dynamics.
However, $\widetilde{\boldsymbol{C}}\left(\boldsymbol{q}, \dot{\boldsymbol{q}}\right)$ potentially contains many thousands of terms, while $\boldsymbol{C}\left(\boldsymbol{q}, \dot{\boldsymbol{q}}\right)\dot{\boldsymbol{q}}$ has significant fewer terms.
If memory serves well, $\widetilde{\boldsymbol{C}}\left(\boldsymbol{q}, \dot{\boldsymbol{q}}\right)$ is the cause of over ninety percent of the computation of Eq.(4).
It also takes most of the symbolic terms in a symbolic expression of Eq.(4).
This is to some extent still true for $\boldsymbol{C}\left(\boldsymbol{q}, \dot{\boldsymbol{q}}\right)\dot{\boldsymbol{q}}$.
Why not getting rid of the Coriolis forces and centripetal forces?
Some people do this, especially if the robot is moving very slow.
Therefore, the simplification is based on significance of each term and dynamic reasoning, which can be easily considered.
The resulting approximation, _e.g._, Eq.(3), can be computed in real time (update rate of the high level controller) and provided insight for control purposes.
Even if the model is an approximation, _i.e._,
$$
\begin{align}
g\left( \int X_\text{flow} \mathrm{d}t, X_\text{flow}, \dfrac{\mathrm{d}}{\mathrm{d}t} X_\text{flow} \right) \approx
\boldsymbol{M}\left(\boldsymbol{q}\right) \ddot{\boldsymbol{q}} +
\boldsymbol{C}\left(\boldsymbol{q}, \dot{\boldsymbol{q}}\right) \dot{\boldsymbol{q}} +
\boldsymbol{g}\left(\boldsymbol{q}\right)
\nonumber
\end{align}
$$
it is quite useful.

Why not just one set of equations for the dynamics?
There are some hybrid systems out there... but this is a different discussion.
So, why do we care about the forward dynamics and inverse dynamics?
It is like $y = f(x)$ versus $x = g(y)$, they are different and have different meaning.
So, when to use the forward dynamics, and when to use the inverse dynamics?
Good question.
The forward dynamics is more or less the robot and, therefore, use the forward dynamics to simulate the robot.
The inverse dynamics, on the other hand, is important for control.

Okay, one last thing I want to mention.
One might wonder why making it super complicated by stating Eq.(1) and Eq.(2)?
Why not jumping to Eq.(3)?
Beside that the effort-flow framework is quite useful and powerful, I did not specify the spaces for Eq.(1) and Eq.(2).
In most textbooks if not all, only Eq.(3) is stated, which limits the discussion on inverse dynamics with respect to the joint space.
In this case, $\dot{\boldsymbol{q}}$ is the joint angle velocity (flow described in the joint space) and $\boldsymbol{\tau}$ is the joint torque (effort described in the joint space).
However, real-world application are mostly described in Task space.
The inverse dynamics expressed in the Task space is different and not expressed by Eq.(3).



---
**Sidenote:**

Note that I did not specify the integral boundaries.
Important to me is the operation and not the specific details, which depend on the implementation.

Both formulations, _i.e._, Eq.(1) and Eq.(2), have their own real-world challenges in measuring certain quantities.
For example, the velocity and time-derivative of a force.