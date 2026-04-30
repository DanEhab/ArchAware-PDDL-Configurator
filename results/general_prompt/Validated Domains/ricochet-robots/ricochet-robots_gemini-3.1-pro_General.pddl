(define (domain ricochet-robots)
(:requirements :strips :typing :negative-preconditions)

(:types
    robot - object
    cell - object
    direction - object
)

(:predicates
    (NEXT ?c - cell ?cnext - cell ?dir - direction)
    (BLOCKED ?c - cell ?dir - direction)
    (at ?r - robot ?c - cell)
    (free ?c - cell)
    (nothing-is-moving)
    (is-moving ?r - robot ?dir - direction)
)

(:action step
    :parameters (?r - robot ?cfrom - cell ?cto - cell ?dir - direction)
    :precondition
        (and
            (is-moving ?r ?dir)
            (at ?r ?cfrom)
            (not (BLOCKED ?cfrom ?dir))
            (NEXT ?cfrom ?cto ?dir)
            (free ?cto)
        )
    :effect
        (and
            (not (at ?r ?cfrom))
            (not (free ?cto))
            (at ?r ?cto)
            (free ?cfrom)
        )
)

(:action stop-at-barrier
    :parameters (?r - robot ?cat - cell ?dir - direction)
    :precondition
        (and
            (is-moving ?r ?dir)
            (at ?r ?cat)
            (BLOCKED ?cat ?dir)
        )
    :effect
        (and
            (not (is-moving ?r ?dir))
            (nothing-is-moving)
        )
)

(:action stop-at-robot
    :parameters (?r - robot ?cat - cell ?cnext - cell ?dir - direction)
    :precondition
        (and
            (is-moving ?r ?dir)
            (at ?r ?cat)
            (NEXT ?cat ?cnext ?dir)
            (not (free ?cnext))
        )
    :effect
        (and
            (not (is-moving ?r ?dir))
            (nothing-is-moving)
        )
)

(:action go
    :parameters (?r - robot ?dir - direction)
    :precondition
        (and
            (nothing-is-moving)
        )
    :effect
        (and
            (not (nothing-is-moving))
            (is-moving ?r ?dir)
        )
)
)