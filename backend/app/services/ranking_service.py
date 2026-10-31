from typing import List, Optional, Any
from ..schemas.place import Place, AgeGroupEnum, DietaryOptionEnum, BudgetTierEnum, CategoryEnum
from ..schemas.recommendation import RecommendationRequest, RankedPlaceItem, RecommendationResponse, ComponentScores
from .places_service import places_service

def resolve_age_group(age: Optional[int], raw_group: Any) -> AgeGroupEnum:
    # 1. If raw_group is an integer or numeric string
    if raw_group is not None:
        try:
            val = int(raw_group)
            if age is None:
                age = val
        except (ValueError, TypeError):
            if isinstance(raw_group, str):
                for ag in AgeGroupEnum:
                    if ag.value.lower() == raw_group.lower():
                        return ag
            elif isinstance(raw_group, AgeGroupEnum):
                return raw_group

    # 2. Resolve numeric age
    if age is not None:
        if age <= 25:
            return AgeGroupEnum.YOUNG_ADULT
        elif age <= 40:
            return AgeGroupEnum.ADULT
        elif age < 60:
            return AgeGroupEnum.FAMILY
        else: # 60 and above
            return AgeGroupEnum.SENIOR

    return AgeGroupEnum.YOUNG_ADULT

def resolve_dietary(raw_diet: Any) -> DietaryOptionEnum:
    if isinstance(raw_diet, DietaryOptionEnum):
        return raw_diet
    if isinstance(raw_diet, str):
        for opt in DietaryOptionEnum:
            if opt.value.lower() == raw_diet.lower():
                return opt
    return DietaryOptionEnum.ALL

def resolve_budget(raw_budget: Any) -> BudgetTierEnum:
    if isinstance(raw_budget, BudgetTierEnum):
        return raw_budget
    if isinstance(raw_budget, str):
        for b in BudgetTierEnum:
            if b.value.lower() == raw_budget.lower():
                return b
    return BudgetTierEnum.MODERATE

class RankingService:
    def rank_places(self, req: RecommendationRequest) -> RecommendationResponse:
        raw_city = (req.city_id or req.city or "").strip().lower()
        city_id = raw_city if raw_city and raw_city not in ["all", "both", "any"] else None
        places = places_service.get_all_places(city_id)

        user_age_group = resolve_age_group(req.age, req.age_group)
        user_diet = resolve_dietary(req.dietary_preference)
        user_budget = resolve_budget(req.budget_tier)
        user_interests = [i.lower() for i in (req.interests or [])]

        ranked_items: List[RankedPlaceItem] = []

        for p in places:
            reasons = []

            # 1. W_category (Weight: 0.45)
            # Calculate Age-Category Affinity
            if user_age_group == AgeGroupEnum.YOUNG_ADULT:
                if p.category in [CategoryEnum.ADVENTURE, CategoryEnum.BEACH, CategoryEnum.CAFE, CategoryEnum.NIGHTLIFE]:
                    affinity = 1.0
                    reasons.append("Vibrant atmosphere popular with young adults (18-25)")
                elif p.category in [CategoryEnum.HERITAGE, CategoryEnum.SPIRITUAL, CategoryEnum.CULTURE]:
                    affinity = 0.6
                else:
                    affinity = 0.4

            elif user_age_group == AgeGroupEnum.ADULT:
                if p.category in [CategoryEnum.HERITAGE, CategoryEnum.CAFE, CategoryEnum.DINING, CategoryEnum.CULTURE]:
                    affinity = 1.0
                    reasons.append("Curated for adults (26-40) seeking culture, dining & heritage")
                elif p.category in [CategoryEnum.BEACH, CategoryEnum.NATURE]:
                    affinity = 0.7
                else:
                    affinity = 0.4

            elif user_age_group == AgeGroupEnum.FAMILY:
                if p.category in [CategoryEnum.NATURE, CategoryEnum.HERITAGE, CategoryEnum.BEACH, CategoryEnum.CULTURE]:
                    affinity = 1.0
                    reasons.append("Family-friendly experience & easy group pacing (41-59)")
                elif p.category in [CategoryEnum.DINING, CategoryEnum.SPIRITUAL]:
                    affinity = 0.7
                else:
                    affinity = 0.3

            else:  # SENIOR (60+)
                if p.category in [CategoryEnum.SPIRITUAL, CategoryEnum.NATURE, CategoryEnum.HERITAGE, CategoryEnum.CULTURE]:
                    affinity = 1.0
                    reasons.append("Serene, tranquil atmosphere ideal for seniors (60+)")
                elif p.category in [CategoryEnum.DINING]:
                    affinity = 0.6
                elif p.category in [CategoryEnum.BEACH, CategoryEnum.CAFE]:
                    affinity = 0.4
                else:
                    affinity = 0.1

            # Match against user interests
            if user_interests:
                cat_match = any(interest in p.category.value.lower() for interest in user_interests)
                tag_match = any(interest in [t.lower() for t in p.tags] for interest in user_interests)
                name_match = any(interest in p.name.lower() for interest in user_interests)
                
                if cat_match or tag_match or name_match:
                    interest_score = 1.0
                    reasons.append("Directly matches your indicated travel interests")
                else:
                    interest_score = 0.2
                w_cat = round(0.5 * affinity + 0.5 * interest_score, 2)
            else:
                w_cat = round(affinity, 2)

            # 2. C_budget (Weight: 0.25)
            if p.budget_tier == user_budget:
                c_bud = 1.0
                reasons.append(f"Exact match with your {user_budget.value.title()} budget")
            elif user_budget == BudgetTierEnum.BUDGET:
                if p.budget_tier == BudgetTierEnum.MODERATE:
                    c_bud = 0.5
                else:  # LUXURY
                    c_bud = 0.1
            elif user_budget == BudgetTierEnum.MODERATE:
                if p.budget_tier == BudgetTierEnum.BUDGET:
                    c_bud = 0.7
                else:  # LUXURY
                    c_bud = 0.6
            elif user_budget == BudgetTierEnum.LUXURY:
                if p.budget_tier == BudgetTierEnum.MODERATE:
                    c_bud = 0.7
                else:  # BUDGET
                    c_bud = 0.4
            else:
                c_bud = 1.0

            # 3. F_dietary (Weight: 0.20)
            if p.category not in [CategoryEnum.CAFE, CategoryEnum.DINING]:
                f_diet = 1.0
            else:
                if user_diet == DietaryOptionEnum.ALL:
                    f_diet = 1.0
                elif user_diet in p.dietary_options:
                    f_diet = 1.0
                    reasons.append(f"Dedicated {user_diet.value.replace('_', ' ').title()} menu available")
                elif user_diet == DietaryOptionEnum.VEGETARIAN and any(opt in p.dietary_options for opt in [DietaryOptionEnum.PURE_VEG_JAIN, DietaryOptionEnum.VEGAN]):
                    f_diet = 1.0
                    reasons.append("Vegetarian-compliant dining options available")
                elif user_diet in [DietaryOptionEnum.PURE_VEG_JAIN, DietaryOptionEnum.HALAL, DietaryOptionEnum.VEGAN]:
                    f_diet = 0.0
                    reasons.append("Dietary mismatch: not certified for your strict diet")
                elif user_diet == DietaryOptionEnum.VEGETARIAN and DietaryOptionEnum.ALL in p.dietary_options:
                    f_diet = 0.3
                else:
                    f_diet = 0.1

            # 4. A_accessibility (Weight: 0.10)
            base_acc = min(1.0, max(0.0, p.accessibility_rating / 5.0))
            if user_age_group == AgeGroupEnum.SENIOR:
                if p.accessibility_rating <= 2:
                    a_acc = 0.0
                    reasons.append("Note: Involves stairs or uneven surfaces (low accessibility)")
                elif p.accessibility_rating >= 4:
                    a_acc = 1.0
                    reasons.append(f"Senior-friendly accessibility rating: {p.accessibility_rating}/5")
                else:
                    a_acc = round(base_acc, 2)
            else:
                a_acc = round(base_acc, 2)

            # MatchScore = [(W_category*0.45)+(C_budget*0.25)+(F_dietary*0.20)+(A_accessibility*0.10)]*100
            score = ((w_cat * 0.45) + (c_bud * 0.25) + (f_diet * 0.20) + (a_acc * 0.10)) * 100.0
            final_score = round(max(0.0, min(100.0, score)), 1)

            if not reasons:
                reasons.append(f"Highly recommended {p.category.value.title()} highlight in {city_id.title()}")

            comp = ComponentScores(
                w_category=w_cat,
                c_budget=c_bud,
                f_dietary=f_diet,
                a_accessibility=a_acc
            )

            ranked_items.append(
                RankedPlaceItem(
                    place=p,
                    match_score=final_score,
                    component_scores=comp,
                    match_reasons=reasons,
                    crowd_status=p.crowd_tendency.value
                )
            )

        # Sort descending by match_score
        ranked_items.sort(key=lambda x: x.match_score, reverse=True)

        return RecommendationResponse(
            city_id=city_id,
            total_results=len(ranked_items),
            ranked_places=ranked_items,
            applied_preferences={
                "age_group": user_age_group,
                "dietary_preference": user_diet,
                "budget_tier": user_budget,
                "interests": user_interests
            }
        )

ranking_service = RankingService()
