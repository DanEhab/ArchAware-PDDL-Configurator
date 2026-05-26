(define (domain ricochet-robots)
(:requirements :strips :typing :negative-preconditions)

(:types
    robot - object
    cell - object
    direction - object
)

(:predicates
    (at ?r - robot ?c - cell)
    (is-moving ?r - robot ?dir - direction)
    (nothing-is-moving)
    (free ?c - cell)
    (BLOCKED ?c - cell ?dir - direction)
    (NEXT ?c - cell ?cnext - cell ?dir - direction)
)

(:action stop-at-barrier
    :parameters (?r - robot ?cat - cell ?dir - direction)
    :precondition
        (and
            (at ?r ?cat)
            (is-moving ?r ?dir)
            (BLOCKED ?cat ?dir)
        )
    :effect
        (and
            (nothing-is-moving)
            (not (is-moving ?r ?dir))
        )
)

(:action stop-at-robot
    :parameters (?r - robot ?cat - cell ?cnext - cell ?dir - direction)
    :precondition
        (and
            (at ?r ?cat)
            (is-moving ?r ?dir)
            (NEXT ?cat ?cnext ?dir)
            (not (free ?cnext))
        )
    :effect
        (and
            (nothing-is-moving)
            (not (is-moving ?r ?dir))
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
            (is-moving ?r ?dir)
            (not (nothing-is-moving))
        )
)

(:action step
    :parameters (?r - robot ?cfrom - cell ?cto - cell ?dir - direction)
    :precondition
        (and
            (at ?r ?cfrom)
            (is-moving ?r ?dir)
            (free ?cto)
            (NEXT ?cfrom ?cto ?dir)
            (not (BLOCKED ?cfrom ?dir))
        )
    :effect
        (and
            (at ?r ?cto)
            (free ?cfrom)
            (not (at ?r ?cfrom))
            (not (free ?cto))
        )
)
)