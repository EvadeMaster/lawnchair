package app.lawnchair.allapps

import android.content.Context
import app.lawnchair.preferences.PreferenceManager
import com.android.launcher3.allapps.AllAppsGridAdapter.AdapterItem
import com.android.launcher3.allapps.search.DefaultAppSearchAlgorithm
import com.android.launcher3.model.data.AppInfo
import com.android.launcher3.search.StringMatcherUtility
import me.xdrop.fuzzywuzzy.FuzzySearch
import me.xdrop.fuzzywuzzy.algorithms.WeightedRatio
import java.util.*

class LawnchairAppSearchAlgorithm(context: Context) : DefaultAppSearchAlgorithm(context) {

    private val useFuzzySearch by PreferenceManager.getInstance(context).useFuzzySearch

    override fun getResult(
        apps: MutableList<AppInfo>,
        query: String
    ): ArrayList<AdapterItem> {
        return if (useFuzzySearch) {
            fuzzySearch(apps, query)
        } else {
            normalSearch(apps, query)
        }
    }

    private fun normalSearch(apps: List<AppInfo>, query: String): ArrayList<AdapterItem> {
        // Do an intersection of the words in the query and each title, and filter out all the
        // apps that don't match all of the words in the query.
        val queryTextLower = query.lowercase(Locale.getDefault())
        val matcher = StringMatcherUtility.StringMatcher.getInstance()

        val result = apps.asSequence()
            .filter { StringMatcherUtility.matches(queryTextLower, it.title.toString(), matcher) }
            .take(MAX_RESULTS_COUNT)
            .mapIndexed { index, info ->
                LawnchairSearchAdapterProvider.asIcon(index, "", info, index)
            }
            .toCollection(ArrayList())
        return result
    }

    private fun fuzzySearch(apps: List<AppInfo>, query: String): ArrayList<AdapterItem> {
        val matches = FuzzySearch.extractSorted(
            query.lowercase(Locale.getDefault()), apps,
            { it.title.toString() }, WeightedRatio(), 65
        )

        return matches.take(MAX_RESULTS_COUNT)
            .mapIndexed { index, match ->
                LawnchairSearchAdapterProvider.asIcon(index, "", match.referent, index)
            }
            .toCollection(ArrayList())
    }
}
