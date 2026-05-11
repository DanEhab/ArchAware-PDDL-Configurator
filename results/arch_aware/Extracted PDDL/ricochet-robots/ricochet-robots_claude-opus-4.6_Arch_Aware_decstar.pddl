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
    (free ?c - cell)
    (NEXT ?c - cell ?cnext - cell ?dir - direction)
    (BLOCKED ?c - cell ?dir - direction)
    (nothing-is-moving)
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
            (not (at ?r ?cfrom))
            (at ?r ?cto)
            (free ?cfrom)
            (not (free ?cto))
        )
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
            (not (is-moving ?r ?dir))
            (nothing-is-moving)
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
            (is-moving ?r ?dir)
            (not (nothing-is-moving))
        )
)
)