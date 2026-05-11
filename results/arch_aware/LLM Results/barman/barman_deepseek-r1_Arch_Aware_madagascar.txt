(define (domain barman)
  (:requirements :strips :typing)
  (:types hand level beverage dispenser container - object
  	  ingredient cocktail - beverage
          shot shaker - container)
  (:predicates  
    (contains ?c - container ?b - beverage)
    (empty ?c - container)
    (clean ?c - container)
    (used ?c - container ?b - beverage)
    (shaked ?s - shaker)
    (unshaked ?s - shaker)
    (shaker-level ?s - shaker ?l - level)
    (shaker-empty-level ?s - shaker ?l - level)
    (holding ?h - hand ?c - container)
    (handempty ?h - hand)
    (ontable ?c - container)
    (dispenses ?d - dispenser ?i - ingredient)
    (next ?l1 ?l2 - level)
    (cocktail-part1 ?c - cocktail ?i - ingredient)
    (cocktail-part2 ?c - cocktail ?i - ingredient)
  )

  (:action pour-shaker-to-shot
    :parameters (?b - beverage ?d - shot ?h - hand ?s - shaker ?l ?l1 - level)
    :precondition (and (next ?l1 ?l) (empty ?d) (clean ?d) (holding ?h ?s) (shaker-level ?s ?l) (shaked ?s) (contains ?s ?b))
    :effect (and (contains ?d ?b) (shaker-level ?s ?l1) (not (clean ?d)) (not (empty ?d)) (not (shaker-level ?s ?l)))
  )

  (:action shake
    :parameters (?b - cocktail ?d1 ?d2 - ingredient ?s - shaker ?h1 ?h2 - hand)
    :precondition (and (cocktail-part1 ?b ?d1) (cocktail-part2 ?b ?d2) (handempty ?h2) (holding ?h1 ?s) (unshaked ?s) (contains ?s ?d1) (contains ?s ?d2))
    :effect (and (shaked ?s) (contains ?s ?b) (not (unshaked ?s)) (not (contains ?s ?d1)) (not (contains ?s ?d2)))
  )

  (:action pour-shot-to-clean-shaker
    :parameters (?s - shot ?i - ingredient ?d - shaker ?h1 - hand ?l ?l1 - level)
    :precondition (and (next ?l ?l1) (empty ?d) (clean ?d) (holding ?h1 ?s) (shaker-level ?d ?l) (contains ?s ?i))
    :effect (and (contains ?d ?i) (unshaked ?d) (shaker-level ?d ?l1) (empty ?s) (not (contains ?s ?i)) (not (empty ?d)) (not (clean ?d)) (not (shaker-level ?d ?l)))
  )

  (:action pour-shot-to-used-shaker
    :parameters (?s - shot ?i - ingredient ?d - shaker ?h1 - hand ?l ?l1 - level)
    :precondition (and (next ?l ?l1) (unshaked ?d) (holding ?h1 ?s) (shaker-level ?d ?l) (contains ?s ?i))
    :effect (and (contains ?d ?i) (shaker-level ?d ?l1) (empty ?s) (not (contains ?s ?i)) (not (shaker-level ?d ?l)))
  )

  (:action fill-shot
    :parameters (?s - shot ?i - ingredient ?h1 ?h2 - hand ?d - dispenser)
    :precondition (and (dispenses ?d ?i) (handempty ?h2) (holding ?h1 ?s) (empty ?s) (clean ?s))
    :effect (and (contains ?s ?i) (used ?s ?i) (not (empty ?s)) (not (clean ?s)))
  )

  (:action refill-shot
    :parameters (?s - shot ?i - ingredient ?h1 ?h2 - hand ?d - dispenser)
    :precondition (and (dispenses ?d ?i) (handempty ?h2) (holding ?h1 ?s) (empty ?s) (used ?s ?i))
    :effect (and (contains ?s ?i) (not (empty ?s)))
  )

  (:action empty-shot
    :parameters (?h - hand ?p - shot ?b - beverage)
    :precondition (and (holding ?h ?p) (contains ?p ?b))
    :effect (and (empty ?p) (not (contains ?p ?b)))
  )

  (:action clean-shot
    :parameters (?s - shot ?b - beverage ?h1 ?h2 - hand)
    :precondition (and (handempty ?h2) (holding ?h1 ?s) (empty ?s) (used ?s ?b))
    :effect (and (clean ?s) (not (used ?s ?b)))
  )

  (:action empty-shaker
    :parameters (?h - hand ?s - shaker ?b - cocktail ?l ?l1 - level)
    :precondition (and (shaker-empty-level ?s ?l1) (shaker-level ?s ?l) (shaked ?s) (contains ?s ?b) (holding ?h ?s))
    :effect (and (shaker-level ?s ?l1) (empty ?s) (not (shaked ?s)) (not (shaker-level ?s ?l)) (not (contains ?s ?b)))
  )

  (:action clean-shaker
    :parameters (?h1 ?h2 - hand ?s - shaker)
    :precondition (and (handempty ?h2) (holding ?h1 ?s) (empty ?s))
    :effect (clean ?s)
  )

  (:action grasp
    :parameters (?h - hand ?c - container)
    :precondition (and (handempty ?h) (ontable ?c))
    :effect (and (holding ?h ?c) (not (ontable ?c)) (not (handempty ?h)))
  )

  (:action leave
    :parameters (?h - hand ?c - container)
    :precondition (holding ?h ?c)
    :effect (and (handempty ?h) (ontable ?c) (not (holding ?h ?c)))
  )
)